async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed: ${url} (${res.status})`);
  return res.json();
}

async function loadStudentData(studentId) {
  const summaryDiv = document.getElementById("student-summary");
  summaryDiv.textContent = "Loading...";

  try {
    const [summary, enrollData] = await Promise.all([
      fetchJSON("/api/metrics/student-summary"),
      fetchJSONAuth(`/api/students/${encodeURIComponent(studentId)}/enrollments`),
    ]);

    const row = summary.find(r => r.student_id === studentId);

    if (!row && (!enrollData.enrollments || !enrollData.enrollments.length)) {
      summaryDiv.textContent = `No data found for student ID ${studentId}.`;
      return;
    }

    const name = (row && row.name) || enrollData.name || studentId;
    const gpa = row && row.gpa != null ? row.gpa.toFixed(2) : "n/a";
    const major = row && row.major || "";
    const cohort = row && row.cohort_year || "";
    const avgAttendance = row && row.avg_attendance != null
      ? row.avg_attendance.toFixed(1)
      : "0.0";
    const dfwCount = row && row.dfw_count != null ? row.dfw_count : 0;
    const creditsAttempted = row && row.credits_attempted != null
      ? row.credits_attempted.toFixed(1)
      : "0.0";

    let html = `<p><strong>${name}</strong> (${studentId})</p>`;
    html += `<p>Major: ${major || "n/a"} | Cohort: ${cohort || "n/a"} | GPA: ${gpa}</p>`;
    html += `<p>Avg attendance: ${avgAttendance}% | DFW courses: ${dfwCount} | Credits attempted: ${creditsAttempted}</p>`;

    if (enrollData.enrollments && enrollData.enrollments.length) {
      html += `<h3>Enrollments</h3>
        <div class="table-responsive">
        <table class="table table-striped table-sm align-middle">
          <thead class="table-light">
            <tr><th>Term</th><th>Course</th><th>Title</th><th>Grade</th><th>Attendance</th></tr>
          </thead><tbody>`;
      enrollData.enrollments.forEach(e => {
        html += `<tr>
          <td>${e.term}</td>
          <td>${e.course_id}</td>
          <td>${e.title || ""}</td>
          <td>${e.grade ?? ""}</td>
          <td>${e.attendance_pct ?? ""}</td>
        </tr>`;
      });
      html += `</tbody></table></div>`;
    } else {
      html += `<p>No enrollments found.</p>`;
    }

    summaryDiv.innerHTML = html;
  } catch (err) {
    console.error(err);
    // Show more detailed error information when available
    let msg = `Error loading student data: ${err.message}`;
    if (err.status) msg += ` (status ${err.status})`;
    if (err.body) msg += ` -- ${err.body}`;
    summaryDiv.textContent = msg;
  }
}


function initStudentPage() {
  const role = getCurrentRole();
  const username = getCurrentUsername();

  if (role === "student") {
    // Student sees their own record
    loadStudentData(username);
  } else if (role === "admin") {
    // Admin uses the search box in students.html; this function is called on click
    const input = document.getElementById("admin-student-id");
    const btn = document.getElementById("admin-student-load");

    if (btn && input) {
      btn.addEventListener("click", () => {
        const id = input.value.trim();
        if (!id) {
          alert("Please enter a student ID.");
          return;
        }
        loadStudentData(id);
      });
      document.getElementById("student-summary").textContent =
        "Enter a student ID above and click Load student.";
    }
  }
}

initStudentPage();

 