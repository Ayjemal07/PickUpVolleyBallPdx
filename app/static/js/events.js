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

    // Open the modal for creating events
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
    

    // Open the modal for editing an event


    function openEditEventModal(event) {
        const modal = document.getElementById("editEventModal");
    
        document.getElementById("editEventId").value = event.id;
        document.getElementById("editTitle").value = event.title;
        document.getElementById("editDescription").value = event.description;
        document.getElementById("editDate").value = event.start.split("T")[0]; 
    
        // Convert datetime format to HH:MM
        const startTime = new Date(event.start).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
        const endTime = new Date(event.end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
    
        document.getElementById("editStartTime").value = startTime;
        document.getElementById("editEndTime").value = endTime;
        document.getElementById("editLocation").value = event.location;
    
        modal.style.display = "block";
    }
    
    
    // Close the Edit Modal when clicking the close button
    document.getElementById("closeEditModal").addEventListener("click", function () {
        document.getElementById("editEventModal").style.display = "none";
    });

    document.getElementById("editEventForm").addEventListener("submit", function (e) {
        e.preventDefault();
    
        const eventId = document.getElementById("editEventId").value;
        const updatedEvent = {
            title: document.getElementById("editTitle").value,
            description: document.getElementById("editDescription").value,
            date: document.getElementById("editDate").value,
            start_time: `${document.getElementById("editStartTime").value}`,
            end_time: `${document.getElementById("editEndTime").value}`,
            location: document.getElementById("editLocation").value,
        };
    
        console.log("Submitting updated event:", updatedEvent); // Debugging
    
        fetch(`/events/edit/${eventId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(updatedEvent),
        })
        .then(response => response.json())
        .then(data => {
            alert("Event updated successfully!");
            location.reload();
        })
        .catch(err => {
            console.error("Error updating event:", err); // Debugging
            alert(`Error updating event: ${err.message}`);
        });
    
        document.getElementById("editEventModal").style.display = "none";
    });
    
    
    

    // Handle event actions (add, edit, delete, cancel)
    function handleEventActions(eventId, action, eventData = null) {
        let url = `/events/${action}/${eventId}`;
        
        let method = action === 'edit' || action === 'add' ? 'POST' : 'POST'; // Ensure all use POST
    
        // Perform fetch request to interact with the backend
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: eventData ? JSON.stringify(eventData) : null,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}`);
            }
            return response.json(); 
        })
        .then(data => {
            alert(`${action.charAt(0).toUpperCase() + action.slice(1)} successful.`);
            location.reload();  // Refresh to show changes
        })
        .catch(err => {
            console.error("Delete action failed:", err); // Log for debugging
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
            // Ensure formatted_date is always used, fallback to "Date Missing"
            const formattedDate = event.formatted_date ? event.formatted_date : 'Date Missing';    
            let eventCardHTML = `
                <div class="event-card">
                    <div class="event-header">
                        <p class="event-date">${formattedDate}</p>  <!-- This must display the date -->
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
            const eventCard = document.createElement('div');
            eventCard.innerHTML = eventCardHTML;
            eventsContainer.appendChild(eventCard);
        });
    
        // **Reattach Event Listeners After Rendering**
        attachEventListeners();
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

    function attachEventListeners() {
        document.querySelectorAll('.edit-event').forEach(button => {
            button.addEventListener('click', function () {
                const eventId = this.getAttribute('data-event-id');
                console.log("Edit button clicked, event ID:", eventId);
    
                const selectedEvent = eventsData.find(e => e.id == Number(eventId));
                if (selectedEvent) {
                    console.log("Editing Event:", selectedEvent);
                    openEditEventModal(selectedEvent);
                } else {
                    console.error("Event not found for ID:", eventId);
                    console.log("Available events:", eventsData);
                }
            });
        });
    
        document.querySelectorAll('.delete-event').forEach(button => {
            button.addEventListener('click', function () {
                const eventId = this.getAttribute('data-event-id');
                handleEventActions(eventId, 'delete');
            });
        });
    
        document.querySelectorAll('.cancel-event').forEach(button => {
            button.addEventListener('click', function () {
                const eventId = this.getAttribute('data-event-id');
                handleEventActions(eventId, 'cancel');
            });
        });
    }
    

    const sortedEvents = sortEventsByDate(eventsData);
    renderEventCards(sortedEvents);
    attachEventListeners(); // Fix for lost event listeners!

});
