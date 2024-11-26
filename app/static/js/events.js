document.addEventListener('DOMContentLoaded', function () {
    if (typeof FullCalendar !== 'undefined') {
        console.log("FullCalendar is loaded");
    } else {
        console.log("FullCalendar is NOT loaded");
    }

    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: '/api/events',  // Your endpoint for fetching events
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        }
    });

    calendar.render();

    // Modal logic
    const createEventModal = document.getElementById("createEventModal");
    const createEventForm = document.getElementById("createEventForm");

    function openCreateEventModal(date) {
        createEventModal.classList.add("active");
        createEventForm.date_time.value = date + "T12:00";
    }

    document.querySelectorAll(".closeModal").forEach((btn) =>
        btn.addEventListener("click", () => {
            createEventModal.classList.remove("active");
        })
    );

    // Handle form submission
    createEventForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        const formData = new FormData(createEventForm);
        const data = Object.fromEntries(formData.entries());

        try {
            await axios.post("/admin/events", data);
            alert("Event created successfully!");
            createEventModal.classList.remove("active");
            calendar.refetchEvents(); // Refresh events on the calendar
        } catch (error) {
            console.error(error);
            alert("Error creating event.");
        }
    });
});
