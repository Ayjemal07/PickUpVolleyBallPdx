document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');

    if (!calendarEl) {
        console.error("Calendar element not found.");
        return;
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: eventsData,
        selectable: userRole === 'admin',
        dateClick: function (info) {
            if (userRole === 'admin') {
                openCreateEventModal(info.dateStr);
            }
        },
        headerToolbar: {
            left: 'prev,next',
            center: 'title',
            right: '',
        },
    });

    calendar.render();


    //admin event adding modal;

    if (userRole === 'admin') {
        document.getElementById('addEventButton').addEventListener('click', function () {
            openCreateEventModal();
        });
    }

    function openCreateEventModal(date) {
        const modal = document.getElementById('createEventModal');
        const eventDateInput = document.getElementById('eventDate');
        modal.style.display = 'block';

        if (date) {
            eventDateInput.value = date;
        }

        document.getElementById('closeModal').onclick = function () {
            modal.style.display = 'none';
        };
    }
});

//events sorting and displaying.

document.addEventListener('DOMContentLoaded', function () {
    const userRole = "{{ user_role }}";

    function sortEventsByDate(events) {
        return events.sort((a, b) => new Date(a.start) - new Date(b.start));
    }

    function renderEventCards(sortedEvents) {
        const eventsContainer = document.querySelector('.events-container');
        eventsContainer.innerHTML = ''; // Clear existing content

        sortedEvents.forEach(event => {
            const eventCard = document.createElement('div');
            eventCard.classList.add('event-card');

            // Format date with "Today", "Tomorrow", or regular date
            const formattedDate = formatEventDate(event.start);

            eventCard.innerHTML = `
                <div class="event-header">
                    <p class="event-date">${formattedDate}</p>
                    <h2 class="event-title">${event.title}</h2>
                </div>
                <div class="event-body">
                    <img src="${event.image_url || ''}" alt="Event image" class="event-image" />
                    <p class="event-location"><strong>Where:</strong> ${event.location}</p>
                    <p class="event-going"><strong>Who's Going:</strong> ${event.going_count || 0} going</p>
                </div>
            `;
            eventsContainer.appendChild(eventCard);
        });
    }

    function formatEventDate(dateString) {
        const eventDate = new Date(dateString);
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Normalize to start of today
        const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000); // Normalize to start of tomorrow
    
        // Format time (e.g., 10:00 AM PST)
        const timeString = eventDate.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
        });
        const timeZone = 'PST'; // Add your timezone abbreviation if required
    
        if (eventDate.getTime() >= today.getTime() && eventDate.getTime() < tomorrow.getTime()) {
            return `Today • ${timeString} ${timeZone}`;
        }
        if (eventDate.getTime() >= tomorrow.getTime() && eventDate.getTime() < tomorrow.getTime() + 24 * 60 * 60 * 1000) {
            return `Tomorrow • ${timeString} ${timeZone}`;
        }
    
        // Format other dates (e.g., Wednesday, January 3 • 10:00 AM PST)
        return `${eventDate.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'long',
            day: 'numeric',
        })} • ${timeString} ${timeZone}`;
    }

    const sortedEvents = sortEventsByDate(eventsData);
    renderEventCards(sortedEvents);
});


document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("addEventForm");
    const successMessage = document.getElementById("successMessage");

    // Listen for the form submission
    form.addEventListener("submit", async (event) => {
        event.preventDefault(); // Prevent the default form submission

        // Gather form data
        const formData = new FormData(form);

        // Send the form data via Fetch API or similar (replace with your backend implementation)
        try {
            const response = await fetch("/events", {
                method: "POST",
                body: formData,
            });

            if (response.ok) {
                // Show the success message
                successMessage.style.display = "block";

                // Optionally, reset the form
                form.reset();

                // Hide the modal after a delay (optional)
                setTimeout(() => {
                    successMessage.style.display = "none";
                    document.getElementById("createEventModal").style.display = "none";
                }, 3000);
            } else {
                // Handle errors (optional)
                alert("Failed to add event. Please try again.");
            }
        } catch (error) {
            console.error("Error adding event:", error);
            alert("An error occurred. Please try again.");
        }
    });
});
