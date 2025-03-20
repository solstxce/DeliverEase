// Flash message handling with SweetAlert
document.addEventListener('DOMContentLoaded', function() {
    const messages = document.querySelectorAll('[data-flash-message]');
    messages.forEach(message => {
        const type = message.dataset.flashType;
        const text = message.dataset.flashMessage;
        
        Swal.fire({
            text: text,
            icon: type === 'error' ? 'error' : 'success',
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
    });
});

// Confirmation dialogs
function confirmAction(message, formId) {
    Swal.fire({
        title: 'Are you sure?',
        text: message,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Yes, proceed!'
    }).then((result) => {
        if (result.isConfirmed) {
            document.getElementById(formId).submit();
        }
    });
    return false;
} 