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
                openCreateEventModal(info.dateStr);  // Open the modal with the clicked date
            }
        },
        headerToolbar: {
            left: 'prev,next',
            center: 'title',
            right: '',
        },
    });

    calendar.render();

    const addEventButton = document.getElementById('addEventButton');
    if (addEventButton) {
        addEventButton.addEventListener('click', function () {
            openCreateEventModal();  // Open modal for a new event
        });
    }

    // Open the modal for creating or editing events
    function openCreateEventModal(date = null, event = null) {
        const modal = document.getElementById('createEventModal');
        const eventDateInput = document.getElementById('date');
        const eventStartTimeInput = document.getElementById('startTime');
        const eventEndTimeInput = document.getElementById('endTime');
        const eventTitleInput = document.getElementById('title');
        const eventDescriptionInput = document.getElementById('description');
        const eventLocationInput = document.getElementById('location');

        modal.style.display = 'block';

        // If it's a new event, populate the date
        if (date) {
            eventDateInput.value = date;
            eventStartTimeInput.value = '12:00';  // Default start time
            eventEndTimeInput.value = '12:00';  // Default end time
        }

        // If editing an existing event, populate the fields
        if (event) {
            eventTitleInput.value = event.title;
            eventDescriptionInput.value = event.description;
            eventLocationInput.value = event.location;
            const eventDate = new Date(event.start);
            eventDateInput.value = eventDate.toISOString().split('T')[0]; // Set date in YYYY-MM-DD format
            eventStartTimeInput.value = event.start_time || '12:00'; // Set start time, default to 12:00
            eventEndTimeInput.value = event.end_time || '12:00'; // Set end time, default to 12:00
            eventDateInput.dataset.eventId = event.id;  // Save the event ID for editing
        }

        document.getElementById('closeModal').onclick = function () {
            modal.style.display = 'none';
        };

        // Handle save for event creation or editing
        document.getElementById('saveEventButton').onclick = function () {
            const eventData = {
                title: eventTitleInput.value,
                description: eventDescriptionInput.value,
                location: eventLocationInput.value,
                start: `${eventDateInput.value}T${eventStartTimeInput.value}:00`,
                end: `${eventDateInput.value}T${eventEndTimeInput.value}:00`,
            };

            if (eventDateInput.dataset.eventId) {  // Editing an existing event
                eventData.id = eventDateInput.dataset.eventId;
                handleEventActions(eventData.id, 'edit', eventData);
            } else {  // Adding a new event
                handleEventActions(null, 'add', eventData);
            }
            modal.style.display = 'none';  // Close the modal after saving
        };
    }

    // Handle event actions (add, edit, delete, cancel)
    function handleEventActions(eventId, action, eventData = null) {
        let url = '/events/';
        if (action === 'add') {
            url += 'add';
        } else if (action === 'edit') {
            url += `edit/${eventId}`;
        } else if (action === 'delete') {
            url += `delete/${eventId}`;
        } else if (action === 'cancel') {
            url += `cancel/${eventId}`;
        }

        // Perform fetch request to interact with the backend
        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(eventData),
        })
        .then(response => response.json())
        .then(data => {
            alert(`${action.charAt(0).toUpperCase() + action.slice(1)} successful.`);
            location.reload();  // Reload to reflect changes
        })
        .catch(err => {
            alert(`Error during ${action}: ${err.message}`);
        });
    }

    // Sort events by date
    function sortEventsByDate(events) {
        return events.sort((a, b) => new Date(a.start) - new Date(b.start));
    }

    // Add event listeners for editing, deleting, and canceling
    function renderEventCards(sortedEvents) {
        const eventsContainer = document.querySelector('.events-container');
        eventsContainer.innerHTML = ''; // Clear existing content

        sortedEvents.forEach(event => {
            const eventCard = document.createElement('div');
            eventCard.classList.add('event-card');

            const formattedDate = formatEventDate(event.start);

            let eventCardHTML = `
                <div class="event-header">
                    <p class="event-date">${formattedDate}</p>
                    <h2 class="event-title">${event.title}</h2>
                    <p class="event-times">
                        <strong>Time:</strong> 
                        ${formatEventTime(event.start)} - ${formatEventTime(event.end)}
                    </p>
            `;

            if (userRole === 'admin') {
                eventCardHTML += `
                    <div class="event-menu">
                        <button class="event-menu-button">⋮</button>
                        <div class="event-menu-options">
                            <button class="edit-event" data-event-id="${event.id}">Edit Event</button>
                            <button class="delete-event" data-event-id="${event.id}">Delete Event</button>
                            <button class="cancel-event" data-event-id="${event.id}">Cancel Event</button>
                        </div>
                    </div>
                `;
            }

            eventCardHTML += `
                </div>
                <div class="event-body">
                    <img src="${event.image_url || ''}" alt="Event image" class="event-image" />
                    <p class="event-location"><strong>Where:</strong> ${event.location}</p>
                    <p class="event-going"><strong>Who's Going:</strong> ${event.going_count || 0} going</p>
                    <button class="btn btn-success custom-attend-button">Attend</button>

                </div>
            `;

            eventCard.innerHTML = eventCardHTML;

            // Add event listeners for edit, delete, cancel
            const editButton = eventCard.querySelector('.edit-event');
            const deleteButton = eventCard.querySelector('.delete-event');
            const cancelButton = eventCard.querySelector('.cancel-event');
            
            if (editButton) {
                editButton.addEventListener('click', function () {
                    openCreateEventModal(null, event);
                });
            }
            if (deleteButton) {
                deleteButton.addEventListener('click', function () {
                    handleEventActions(event.id, 'delete');
                });
            }
            if (cancelButton) {
                cancelButton.addEventListener('click', function () {
                    handleEventActions(event.id, 'cancel');
                });
            }

            eventsContainer.appendChild(eventCard);
        });
    }

    // Format event date to show "Today", "Tomorrow", or a full date
    function formatEventDate(dateString) {
        const eventDate = new Date(dateString);
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Normalize to start of today
        const tomorrow = new Date(today.getTime() + 24 * 60 * 60 * 1000); // Normalize to start of tomorrow

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

        return `${eventDate.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'long',
            day: 'numeric',
        })} • ${timeString} ${timeZone}`;
    }

    // Format event time for display
    function formatEventTime(dateString) {
        const eventDate = new Date(dateString);
        return eventDate.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    }

    const sortedEvents = sortEventsByDate(eventsData);
    renderEventCards(sortedEvents);
});
