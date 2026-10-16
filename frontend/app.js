(() => {
  "use strict";

  const defaultApiUrl = `${window.location.origin}/api`;
  const storedApiUrl = localStorage.getItem("skillbridge-api-url");
  let apiBase = (storedApiUrl || defaultApiUrl).replace(/\/+$/, "");
  let students = [];
  let classes = [];
  let myBookings = [];
  let noticeTimer;

  const $ = (selector, root = document) => root.querySelector(selector);
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
  const currentStudent = () => $("#student-select").value;

  function notify(message, isError = false) {
    const notice = $("#notice");
    notice.textContent = message;
    notice.classList.toggle("error", isError);
    notice.classList.remove("hidden");
    window.clearTimeout(noticeTimer);
    noticeTimer = window.setTimeout(() => notice.classList.add("hidden"), 5200);
  }

  async function api(path, options = {}) {
    let response;
    try {
      response = await fetch(`${apiBase}${path}`, options);
    } catch {
      setConnection(false);
      throw new Error(`Can't reach ${apiBase}. Check the API URL and make sure the backend is running.`);
    }
    const payload = response.status === 204 ? null : await response.json().catch(() => null);
    if (!response.ok) {
      const detail = payload && payload.detail;
      throw new Error(typeof detail === "string" ? detail : "The request could not be completed.");
    }
    setConnection(true);
    return payload;
  }

  function setConnection(isOnline) {
    $("#connection-dot").classList.toggle("online", isOnline);
    $("#connection-dot").classList.toggle("offline", !isOnline);
    $("#connection-label").textContent = isOnline ? "Connected" : "Offline";
    $("#footer-api").textContent = apiBase;
  }

  function setView(view) {
    document.querySelectorAll(".view-section").forEach((section) => {
      section.classList.toggle("active", section.id === `view-${view}`);
    });
    document.querySelectorAll(".nav-link").forEach((button) => {
      button.classList.toggle("active", button.dataset.view === view);
    });
    const labels = { home: "Overview", explore: "Explore", learning: "My learning", assistant: "Study assistant" };
    $("#page-label").textContent = labels[view] || "Overview";
    if (view === "learning") refreshBookings();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function renderClasses(target, list) {
    if (!list.length) {
      target.innerHTML = '<div class="empty-state">No sessions match that search just yet.</div>';
      return;
    }
    target.innerHTML = list.map((item, index) => {
      const isBooked = myBookings.some((booking) => booking.id === item.id);
      const full = item.seats_remaining <= 0;
      const needsProfile = !currentStudent();
      return `<article class="class-card">
        <div class="class-topline"><span class="class-symbol">${["⌘", "◈", "⌁", "✳", "⌗"][index % 5]}</span><span class="class-tag">${escapeHtml(item.subject)}</span></div>
        <h3>${escapeHtml(item.title)}</h3>
        <p class="class-meta">With ${escapeHtml(item.tutor)}<br>${escapeHtml(item.slot)} · ${item.average_rating ? `★ ${escapeHtml(item.average_rating)}` : "New session"}</p>
        <div class="class-footer"><span class="capacity">${escapeHtml(item.seats_remaining)} of ${escapeHtml(item.capacity)} seats left</span>
        <button class="button ${isBooked || needsProfile ? "button-outline" : "button-dark"}" data-book="${escapeHtml(item.id)}" ${isBooked || full ? "disabled" : ""}>${isBooked ? "You're in ✓" : full ? "Full" : needsProfile ? "Choose profile to book" : "Book a seat"}</button></div>
      </article>`;
    }).join("");
  }

  function renderStudents(target, list) {
    if (!list.length) {
      target.innerHTML = '<div class="empty-state">No peers found. Try a different skill.</div>';
      return;
    }
    target.innerHTML = list.map((student) => {
      const initials = student.name.split(/\s+/).map((part) => part[0]).slice(0, 2).join("");
      const score = student.ratings.length
        ? (student.ratings.reduce((total, rating) => total + rating.score, 0) / student.ratings.length).toFixed(1)
        : "New";
      return `<article class="student-card">
        <div class="student-top"><span class="student-avatar">${escapeHtml(initials)}</span><div><h3>${escapeHtml(student.name)}</h3><span class="student-availability">${escapeHtml(student.availability)} · ★ ${escapeHtml(score)}</span></div></div>
        <div class="skill-list">${student.skills.map((skill) => `<span class="skill-chip">${escapeHtml(skill)}</span>`).join("")}</div>
      </article>`;
    }).join("");
  }

  function populateProfile() {
    const select = $("#student-select");
    const previous = localStorage.getItem("skillbridge-student");
    select.innerHTML = '<option value="">Choose your profile</option>' + students
      .map((student) => `<option value="${escapeHtml(student.name)}">${escapeHtml(student.name)}</option>`).join("");
    if (students.some((student) => student.name === previous)) select.value = previous;
    populateTutorClasses();
  }

  function populateTutorClasses() {
    const options = classes.map((cls) =>
      `<option value="${escapeHtml(cls.id)}">${escapeHtml(cls.id)} · ${escapeHtml(cls.title)} (${escapeHtml(cls.tutor)})</option>`
    ).join("");
    $("#link-class").innerHTML = options;
    $("#notes-class").innerHTML = options;
  }

  function updateDashboard() {
    $("#stat-classes").textContent = classes.length;
    $("#stat-students").textContent = students.length;
    $("#stat-bookings").textContent = myBookings.length;
    renderClasses($("#home-classes"), classes.slice(0, 3));
    renderClasses($("#all-classes"), classes.filter((item) =>
      `${item.title} ${item.subject} ${item.tutor}`.toLowerCase().includes($("#class-search").value.trim().toLowerCase())
    ));
    renderStudents($("#home-students"), students.slice(0, 4));
    renderStudents($("#all-students"), students.filter((student) =>
      `${student.name} ${student.skills.join(" ")} ${student.interests.join(" ")}`.toLowerCase()
        .includes($("#student-search").value.trim().toLowerCase())
    ));
    $("#stat-bookings").textContent = myBookings.length;
  }

  async function refreshBookings() {
    const name = currentStudent();
    myBookings = name ? await api(`/bookings?student_name=${encodeURIComponent(name)}`) : [];
    renderBookings();
    updateDashboard();
  }

  function renderBookings() {
    const target = $("#my-bookings");
    if (!currentStudent()) {
      target.innerHTML = '<div class="empty-state">Choose a demo profile from the left menu to see your learning sessions.</div>';
      return;
    }
    if (!myBookings.length) {
      target.innerHTML = '<div class="empty-state">No sessions booked yet. Head to Explore and save a seat in something new.</div>';
      return;
    }
    target.innerHTML = myBookings.map((item) => `<article class="learning-card">
      <div class="learning-header"><div><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.id)} · ${escapeHtml(item.subject)} · ${escapeHtml(item.slot)}<br>Peer tutor: ${escapeHtml(item.tutor)}</p></div><span class="class-tag">BOOKED</span></div>
      <div class="learning-actions">
        <button class="button button-outline" data-meeting="${escapeHtml(item.id)}">Join session ↗</button>
        <button class="button button-outline" data-notes="${escapeHtml(item.id)}">View class notes</button>
        <button class="button button-outline" data-ratings="${escapeHtml(item.id)}">Read ratings</button>
      </div>
      <div class="learning-details hidden" data-details="${escapeHtml(item.id)}"></div>
      <form class="rating-form" data-rating-form="${escapeHtml(item.id)}">
        <label class="visually-hidden" for="score-${escapeHtml(item.id)}">Rating</label>
        <select id="score-${escapeHtml(item.id)}" name="score" aria-label="Rating" required><option value="">Rate this session</option><option value="5">★★★★★ — Loved it</option><option value="4">★★★★ — Great</option><option value="3">★★★ — Good</option><option value="2">★★ — Okay</option><option value="1">★ — Needs work</option></select>
        <label class="visually-hidden" for="feedback-${escapeHtml(item.id)}">Feedback</label>
        <input id="feedback-${escapeHtml(item.id)}" name="feedback" maxlength="2000" placeholder="Add a little feedback (optional)">
        <button class="button button-dark button-small" type="submit">Send rating</button>
      </form>
    </article>`).join("");
  }

  async function refresh() {
    const [studentRows, classRows] = await Promise.all([api("/students"), api("/classes")]);
    students = studentRows;
    classes = classRows;
    populateProfile();
    await refreshBookings();
    updateDashboard();
  }

  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.view));
  });
  document.querySelectorAll("[data-go]").forEach((button) => {
    button.addEventListener("click", () => setView(button.dataset.go));
  });

  $("#student-select").addEventListener("change", async (event) => {
    localStorage.setItem("skillbridge-student", event.target.value);
    try {
      await refreshBookings();
    } catch (error) {
      notify(error.message, true);
    }
  });

  $("#class-search").addEventListener("input", updateDashboard);
  $("#student-search").addEventListener("input", updateDashboard);

  document.body.addEventListener("click", async (event) => {
    const bookButton = event.target.closest("[data-book]");
    const meetingButton = event.target.closest("[data-meeting]");
    const notesButton = event.target.closest("[data-notes]");
    const ratingsButton = event.target.closest("[data-ratings]");
    try {
      if (bookButton) {
        if (!currentStudent()) {
          notify("Choose a demo profile from the sidebar before booking a session.");
          $("#student-select").focus();
          return;
        }
        const result = await api("/bookings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ student_name: currentStudent(), class_id: bookButton.dataset.book }),
        });
        notify(`You're booked for ${result.title}. See you there!`);
        await refresh();
      } else if (meetingButton) {
        const result = await api(`/classes/${encodeURIComponent(meetingButton.dataset.meeting)}/meeting?student_name=${encodeURIComponent(currentStudent())}`);
        window.open(result.url, "_blank", "noopener,noreferrer");
      } else if (notesButton || ratingsButton) {
        const button = notesButton || ratingsButton;
        const id = button.dataset.notes || button.dataset.ratings;
        const isNotes = Boolean(notesButton);
        const endpoint = isNotes ? "notes" : "ratings";
        const query = isNotes ? `?student_name=${encodeURIComponent(currentStudent())}` : "";
        const results = await api(`/classes/${encodeURIComponent(id)}/${endpoint}${query}`);
        const details = $(`[data-details="${CSS.escape(id)}"]`);
        details.classList.remove("hidden");
        details.innerHTML = results.length
          ? results.map((item) => isNotes
            ? `<strong>Published ${escapeHtml(item.published_at)}</strong>\n${escapeHtml(item.summary)}`
            : `<strong>${escapeHtml(item.score)}/5 · ${escapeHtml(item.student)}</strong>\n${escapeHtml(item.feedback || "No written feedback.")}`
          ).join("\n\n")
          : isNotes ? "No study notes have been shared yet." : "No one has rated this session yet.";
      }
    } catch (error) {
      notify(error.message, true);
    }
  });

  document.body.addEventListener("submit", async (event) => {
    const form = event.target.closest("[data-rating-form]");
    if (!form) return;
    event.preventDefault();
    const formData = new FormData(form);
    try {
      await api(`/classes/${encodeURIComponent(form.dataset.ratingForm)}/ratings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_name: currentStudent(),
          score: Number(formData.get("score")),
          feedback: formData.get("feedback"),
        }),
      });
      notify("Thanks for sharing your feedback!");
      await refresh();
      setView("learning");
    } catch (error) {
      notify(error.message, true);
    }
  });

  $("#ask-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const question = $("#question-input").value.trim();
    if (!question) return;
    const messages = $("#chat-messages");
    messages.insertAdjacentHTML("beforeend", `<div class="chat-bubble user-bubble">${escapeHtml(question)}</div>`);
    $("#question-input").value = "";
    const pending = document.createElement("div");
    pending.className = "chat-bubble assistant-bubble";
    pending.textContent = "Thinking it through…";
    messages.append(pending);
    messages.scrollTop = messages.scrollHeight;
    try {
      const result = await api("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      pending.textContent = result.answer;
    } catch (error) {
      pending.textContent = error.message;
      pending.classList.add("error");
    }
  });

  $("#tutor-link-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const id = $("#link-class").value;
    const cls = classes.find((item) => item.id === id);
    try {
      const result = await api(`/classes/${encodeURIComponent(id)}/meeting-link`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tutor_name: currentStudent(), link: $("#meeting-link").value.trim() }),
      });
      notify(result.message);
      $("#meeting-link").value = "";
    } catch (error) {
      notify(error.message || `Choose the tutor profile for ${cls ? cls.tutor : "this session"}.`, true);
    }
  });

  $("#notes-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const id = $("#notes-class").value;
    const audio = $("#audio-file").files[0];
    if (!audio) {
      notify("Choose a recording first.", true);
      return;
    }
    const formData = new FormData();
    formData.set("tutor_name", currentStudent());
    formData.set("audio", audio);
    try {
      const result = await api(`/classes/${encodeURIComponent(id)}/notes`, { method: "POST", body: formData });
      notify(result.message);
      $("#notes-form").reset();
    } catch (error) {
      notify(error.message, true);
    }
  });

  $("#settings-button").addEventListener("click", () => {
    $("#settings-panel").classList.toggle("hidden");
    $("#api-url").value = apiBase;
  });
  $("#save-api-url").addEventListener("click", async () => {
    const value = $("#api-url").value.trim().replace(/\/+$/, "").replace(/\/api$/i, "");
    if (!/^https?:\/\//i.test(value)) {
      notify("Enter a valid backend URL, including https:// or http://.", true);
      return;
    }
    apiBase = `${value}/api`;
    localStorage.setItem("skillbridge-api-url", apiBase);
    try {
      await refresh();
      $("#settings-panel").classList.add("hidden");
      notify("Connected to your SkillBridge backend.");
    } catch (error) {
      notify(error.message, true);
    }
  });

  refresh().catch((error) => {
    setConnection(false);
    notify(error.message, true);
    $("#home-classes").innerHTML = '<div class="empty-state">Start the SkillBridge API, then refresh this page to load sessions.</div>';
    $("#home-students").innerHTML = '<div class="empty-state">The student directory will appear once the API is connected.</div>';
  });
})();
