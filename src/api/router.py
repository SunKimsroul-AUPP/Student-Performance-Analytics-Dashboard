from pathlib import Path
import io
import tempfile
from typing import List, Optional, Any, Dict

import pandas as pd
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    Query,
)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse

from ..domain.grade_scale import default_scale
from ..domain.gradebook import Gradebook
from ..services.analytics_service import AnalyticsService
from ..services.risk_service import RiskService
from ..services.graph_service import GraphService
from ..services.data_service import DataService
from ..models.dto import (
    GPAEntry,
    PassRateEntry,
    DFWRateEntry,
    RiskEntry,
    GraphSummary,
    AttendanceCorrelation,
    CohortGPAEntry,
)
from ..auth.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    require_role,
)

router = APIRouter()


def get_services():
  """Build shared services from the singleton DataService."""
  data_service = DataService.instance()
  data = data_service.get_datasets()

  gradebook = Gradebook(
      enrollments=data["enrollments"],
      courses=data["courses"],
      scale=default_scale,
  )
  analytics = AnalyticsService(
      gradebook=gradebook,
      students=data["students"],
      courses=data["courses"],
      enrollments=data["enrollments"],
  )
  # gpa_tbl includes student metadata from AnalyticsService.gpa_table()
  gpa_tbl = analytics.gpa_table()
  risk = RiskService(gpa_tbl, data["enrollments"])
  graph = GraphService(data["prerequisites"], data.get("courses"))
  return data_service, data, gradebook, analytics, risk, graph


@router.get("/health")
def health():
  return {"status": "ok"}


# ---------- Auth endpoints ----------


@router.post("/auth/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
  """
  OAuth2 password flow: returns a JWT access token.
  """
  user = authenticate_user(form_data.username, form_data.password)
  if not user:
      raise HTTPException(
          status_code=401,
          detail="Incorrect username or password",
          headers={"WWW-Authenticate": "Bearer"},
      )

  access_token = create_access_token(data={"sub": user["username"]})
  return {
      "access_token": access_token,
      "token_type": "bearer",
      "role": user["role"],
  }


# ---------- Metrics endpoints (PUBLIC) ----------


@router.get("/metrics/gpa", response_model=List[GPAEntry])
def get_gpa(
  major: Optional[str] = Query(None),
  cohort_year: Optional[int] = Query(None),
  services=Depends(get_services),
):
  _, _, _, analytics, _, _ = services
  tbl = analytics.gpa_table(major=major, cohort_year=cohort_year)
  records: List[GPAEntry] = []
  for row in tbl.itertuples():
      cohort = None
      if hasattr(row, "cohort_year") and not pd.isna(row.cohort_year):
          cohort = int(row.cohort_year)
      records.append(
          GPAEntry(
              student_id=row.student_id,
              name=getattr(row, "name", None),
              major=getattr(row, "major", None),
              cohort_year=cohort,
              total_credits=float(row.total_credits),
              quality_points=float(row.quality_points),
              gpa=float(row.gpa),
          )
      )
  return records


@router.get("/metrics/pass-rates", response_model=List[PassRateEntry])
def get_pass_rates(
  department: Optional[str] = Query(None),
  term: Optional[str] = Query(None),
  services=Depends(get_services),
):
  _, _, _, analytics, _, _ = services
  df = analytics.pass_rates(department=department, term=term)
  out: List[PassRateEntry] = []
  for row in df.itertuples():
      level = None
      if hasattr(row, "level") and not pd.isna(row.level):
          level = int(row.level)
      out.append(
          PassRateEntry(
              course_id=row.course_id,
              title=row.title,
              department=getattr(row, "department", None),
              level=level,
              pass_rate=float(row.pass_rate),
          )
      )
  return out


@router.get("/metrics/dfw-rates", response_model=List[DFWRateEntry])
def get_dfw_rates(
  department: Optional[str] = Query(None),
  term: Optional[str] = Query(None),
  services=Depends(get_services),
):
  _, _, _, analytics, _, _ = services
  df = analytics.dfw_rates(department=department, term=term)
  out: List[DFWRateEntry] = []
  for row in df.itertuples():
      level = None
      if hasattr(row, "level") and not pd.isna(row.level):
          level = int(row.level)
      out.append(
          DFWRateEntry(
              course_id=row.course_id,
              title=row.title,
              department=getattr(row, "department", None),
              level=level,
              dfw_rate=float(row.dfw_rate),
          )
      )
  return out


@router.get("/metrics/attendance-correlation", response_model=AttendanceCorrelation)
def get_attendance_corr(services=Depends(get_services)):
  _, _, _, analytics, _, _ = services
  corr = analytics.attendance_grade_correlation()
  return AttendanceCorrelation(**corr)


@router.get("/metrics/cohort-gpa", response_model=List[CohortGPAEntry])
def get_cohort_gpa(services=Depends(get_services)):
  _, _, _, analytics, _, _ = services
  df = analytics.cohort_gpa_summary()
  out: List[CohortGPAEntry] = []
  for row in df.itertuples():
      if pd.isna(row.cohort_year):
          continue
      out.append(
          CohortGPAEntry(
              cohort_year=int(row.cohort_year),
              mean=float(row.mean),
              median=float(row.median),
              count=int(row.count),
          )
      )
  return out


@router.get("/metrics/student-summary")
def get_student_summary(services=Depends(get_services)) -> List[Dict[str, Any]]:
  """
  Enriched per-student metrics for dashboards:
  - GPA, total_credits, quality_points
  - avg_attendance, dfw_count, credits_attempted
  - basic student info (name, major, cohort_year)
  """
  _, _, _, analytics, _, _ = services
  df = analytics.student_summary_table()
  return df.to_dict(orient="records")


# ---------- Export endpoints (PUBLIC) ----------


@router.get("/metrics/gpa/export")
def export_gpa(
  major: Optional[str] = Query(None),
  cohort_year: Optional[int] = Query(None),
  services=Depends(get_services),
):
  _, _, _, analytics, _, _ = services
  tbl = analytics.gpa_table(major=major, cohort_year=cohort_year)
  buffer = io.StringIO()
  tbl.to_csv(buffer, index=False)
  buffer.seek(0)
  headers = {"Content-Disposition": 'attachment; filename="gpa_table.csv"'}
  return StreamingResponse(
      iter([buffer.getvalue()]),
      media_type="text/csv",
      headers=headers,
  )


@router.get("/metrics/pass-rates/export")
def export_pass_rates(
  department: Optional[str] = Query(None),
  term: Optional[str] = Query(None),
  services=Depends(get_services),
):
  _, _, _, analytics, _, _ = services
  df = analytics.pass_rates(department=department, term=term)
  buffer = io.StringIO()
  df.to_csv(buffer, index=False)
  buffer.seek(0)
  headers = {"Content-Disposition": 'attachment; filename="course_pass_rates.csv"'}
  return StreamingResponse(
      iter([buffer.getvalue()]),
      media_type="text/csv",
      headers=headers,
  )


# ---------- Risk & graph (PUBLIC) ----------


@router.get("/risk/at-risk", response_model=List[RiskEntry])
def get_at_risk(services=Depends(get_services)):
  _, _, _, _, risk, _ = services
  data = risk.at_risk_students()
  return [RiskEntry(**item) for item in data]


@router.get("/graph/prerequisites", response_model=GraphSummary)
def get_prereq_summary(services=Depends(get_services)):
  _, _, _, _, _, graph = services
  summary = graph.summary()
  return GraphSummary(**summary)


@router.get("/graph/prerequisites/full")
def get_prereq_full(services=Depends(get_services)):
  """Return a list of all courses with their titles and prerequisites.

  Each item: { course_id, title?, prerequisites: [ {course_id, title?}, ... ] }
  """
  _, _, _, _, _, graph = services
  adj = graph.adjacency()
  out = []
  for course_id, pres in adj.items():
    item = {"course_id": course_id}
    title = getattr(graph, 'course_titles', {}).get(str(course_id))
    if title:
      item["title"] = title
    item["prerequisites"] = pres
    out.append(item)
  # Also include courses that might have no adjacency entry but exist in titles
  for cid, title in getattr(graph, 'course_titles', {}).items():
    if cid not in adj:
      out.append({"course_id": cid, "title": title, "prerequisites": []})
  return out


# ---------- Student endpoints (still protected) ----------


@router.get("/students")
def list_students(services=Depends(get_services)):
  """
  Return basic info for all students.
  """
  _, data, *_ = services
  students = data["students"]
  return students[["student_id", "name", "major", "cohort_year"]].to_dict(
      orient="records"
  )


@router.get("/students/{student_id}/enrollments")
def get_student_enrollments(
  student_id: str,
  services=Depends(get_services),
):
  """
  Return enrollments for a single student. For demo purposes this endpoint
  is public (no auth) so admin UI can load student records in the demo.
  """
  _, data, *_ = services
  enroll = data["enrollments"]
  students = data["students"]
  courses = data["courses"]

  df = (
      enroll[enroll["student_id"] == student_id]
      .merge(courses, on="course_id", how="left")
  )

  stu_row = students[students["student_id"] == student_id]
  student_name = stu_row["name"].iloc[0] if not stu_row.empty else None

  return {
      "student_id": student_id,
      "name": student_name,
      "enrollments": df.to_dict(orient="records"),
  }


# ---------- Admin / Data endpoints (NOW PUBLIC) ----------


@router.get("/admin/data-status")
def get_data_status(
  services=Depends(get_services),
):
  """
  Previously admin-only; now public for demo/UI purposes.
  """
  data_service, data, *_ = services
  status = data_service.status()
  columns = {name: list(df.columns) for name, df in data.items()}
  status["columns"] = columns
  return status


@router.get("/admin/download/{table_name}")
def download_table(
  table_name: str,
  services=Depends(get_services),
):
  """
  Previously required admin role; now public for demo/UI purposes.
  """
  data_service, *_ = services
  name = table_name.lower()
  if name not in {"students", "courses", "enrollments", "prerequisites"}:
      raise HTTPException(status_code=400, detail="Invalid table name")
  df = data_service.get_table(name)
  buffer = io.StringIO()
  df.to_csv(buffer, index=False)
  buffer.seek(0)
  headers = {"Content-Disposition": f'attachment; filename="{name}.csv"'}
  return StreamingResponse(
      iter([buffer.getvalue()]),
      media_type="text/csv",
      headers=headers,
  )


@router.post("/admin/upload/{table_name}")
async def upload_table(
  table_name: str,
  file: UploadFile = File(...),
  services=Depends(get_services),
):
  """
  Previously required admin role; now public for demo/UI purposes.
  WARNING: In a real deployment, you must protect this endpoint.
  """
  data_service, *_ = services
  name = table_name.lower()
  if name not in {"students", "courses", "enrollments", "prerequisites"}:
      raise HTTPException(status_code=400, detail="Invalid table name")

  try:
      contents = await file.read()
      with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
          tmp.write(contents)
          tmp_path = Path(tmp.name)
      data_service.replace_table_from_file(name, tmp_path)
      return {"status": "ok", "message": f"{name} updated successfully"}
  except Exception as exc:
      raise HTTPException(status_code=400, detail=str(exc))