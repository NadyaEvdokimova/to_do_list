function toggle_display(){
  var el = document.querySelector('.hid_form');

  if(el.style.visibility == 'hidden'){
      el.style.visibility = 'visible'
      el.style.display = "inline-block"
  }else{
     el.style.visibility = 'hidden'
     el.style.display = "none"
  }
}

function cross_text(taskId) {
  var taskElement = document.getElementById('task_' + taskId);
        taskElement.classList.toggle('line-through');
}

document.addEventListener('click', function(event) {
    var taskId = event.target.getAttribute('data-task-id');
    if (!taskId) return;

    var taskElement = document.getElementById('task_' + taskId);
    var taskElementDate = document.getElementById('due_date_' + taskId);
    var saveButton = document.getElementById('save_button_' + taskId);

    var isTaskClicked = event.target === taskElement || taskElement.contains(event.target);
    var isDateClicked = event.target === taskElementDate || taskElementDate.contains(event.target);

    if (isTaskClicked || isDateClicked) {
        saveButton.style.display = 'inline-block';
    } else {
        saveButton.style.display = 'none';
    }
});


function saveTask(taskId) {
    var taskElement = document.getElementById('task_' + taskId);
    var taskElementDate = document.getElementById('due_date_' + taskId);
    var saveButton = document.getElementById('save_button_' + taskId);
    var newTaskText = taskElement.innerText;
    var newTaskDueDate = taskElementDate.innerText;


    // Send the updated task text to the server using AJAX
    fetch('/edit_task/' + taskId, {
        method: 'PATCH',
        body: JSON.stringify({ task_text: newTaskText, due_date: newTaskDueDate }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Task text updated successfully:', data);
        saveButton.style.display = 'none';
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Get all elements with class "due_date"
    var dueDateElements = document.querySelectorAll('.due_date span');

    // Loop through each due date element
    dueDateElements.forEach(function(element) {
        // Get the due date from the element's inner text
        var dueDate = new Date(element.innerText);

        // Calculate the difference between due date and current date
        var timeDiff = dueDate.getTime() - Date.now();
        var daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24));

        // Add a class to change color if due date is close
        if (daysDiff <= 3) {
            element.classList.add('due-date-close');
        }
    });
});