document.addEventListener('DOMContentLoaded', function () {
    if (typeof FullCalendar !== 'undefined') {
        console.log("FullCalendar is loaded");
    } else {
        console.error("FullCalendar is NOT loaded");
        return;
    }

    // Initialize calendar
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) {
        console.error("Calendar element with id 'calendar' not found.");
        return;
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: '/api/events', // Your endpoint for fetching events
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        dateClick: function (info) {
            // Open the modal to create an event with the clicked date prefilled
            const createEventModal = document.getElementById("createEventModal");
            if (createEventModal) {
                createEventModal.classList.add("active");

                const eventDateInput = document.getElementById("eventDate");
                if (eventDateInput) {
                    eventDateInput.value = info.dateStr; // Prefill the date
                    console.log("Date prefilled:", info.dateStr);
                } else {
                    console.error("Event date input field not found.");
                }
            } else {
                console.error("Create event modal not found.");
            }
        },
        eventClick: function (info) {
            // Open the edit modal with event details for editing
            const editEventModal = document.getElementById("editEventModal");
            if (editEventModal) {
                editEventModal.classList.add("active");

                const event = info.event;
                document.getElementById("editEventName").value = event.title;
                document.getElementById("editEventDate").value = event.start.toISOString().split('T')[0]; // Format date
                document.getElementById("editEventDescription").value = event.extendedProps.description;
                document.getElementById("editEventLocation").value = event.extendedProps.location;
                document.getElementById("editEventLevel").value = event.extendedProps.level;
                document.getElementById("eventId").value = event.id; // Store event ID for deletion or update
            } else {
                console.error("Edit event modal not found.");
            }
        }
    });

    calendar.render();

    // Handle `touchmove` event to prevent non-passive warnings
    const handleTouchMove = (e) => {
        e.preventDefault();
    };

    const addTouchEventListener = (element) => {
        element.addEventListener('touchmove', handleTouchMove, { passive: false });
    };

    // Apply to relevant elements
    addTouchEventListener(calendarEl);

    // Modal and form logic for creating an event
    const createEventModal = document.getElementById("createEventModal");
    const createEventForm = document.getElementById("createEventForm");

    if (createEventModal && createEventForm) {
        // Close modal
        const closeModalButtons = document.querySelectorAll(".closeModal");
        if (closeModalButtons.length > 0) {
            closeModalButtons.forEach((btn) =>
                btn.addEventListener("click", () => {
                    createEventModal.classList.remove("active");
                })
            );
        } else {
            console.warn("No .closeModal buttons found in the DOM.");
        }

        // Handle event creation form submission
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
    } else {
        console.warn("Modal or form elements not found.");
    }

    // Event deletion logic
    const deleteEventButton = document.getElementById("deleteEventButton");
    if (deleteEventButton) {
        deleteEventButton.addEventListener("click", async function () {
            const eventId = document.getElementById("eventId").value; // Hidden input with the event ID
            try {
                await axios.delete(`/api/events/${eventId}`);
                alert("Event deleted successfully");
                calendar.refetchEvents();
            } catch (error) {
                console.error(error);
                alert("Error deleting event.");
            }
        });
    }

    // RSVP functionality (Event Sign-up)
    const rsvpButton = document.getElementById("rsvpButton");
    if (rsvpButton) {
        rsvpButton.addEventListener("click", async function () {
            const eventId = document.getElementById("eventId").value; // Get event ID
            // const userId = /* Your logic to get the current user ID */;

            try {
                const response = await axios.post(`/api/events/${eventId}/rsvp`, { userId });
                alert(response.data.message); // Show RSVP success or error message
                calendar.refetchEvents();
            } catch (error) {
                console.error(error);
                alert("Error RSVPing for the event.");
            }
        });
    }

    // Event level filtering (Beginner/Advanced)
    const filterLevel = document.getElementById("filterLevel");
    if (filterLevel) {
        filterLevel.addEventListener("change", function () {
            const selectedLevel = filterLevel.value;
            calendar.refetchEvents(); // Fetch events again after filtering
        });
    }
});
