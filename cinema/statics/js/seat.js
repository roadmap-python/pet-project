document.addEventListener('DOMContentLoaded', () => {
    const seats = document.querySelectorAll('.seat:not(.sold)');
    const selectedSeatsElement = document.getElementById('selected-seats');
    const totalPriceElement = document.getElementById('total-price');
    
    // Giả định giá
    const ticketPriceNormal = 80000;
    const ticketPriceVIP = 120000;

    function updateSelection() {
        const selectedSeats = document.querySelectorAll('.seat.selected');
        let totalPrice = 0;
        let seatCount = selectedSeats.length;

        selectedSeats.forEach(seat => {
            if (seat.classList.contains('VIP')) {
                totalPrice += ticketPriceVIP;
            } else {
                totalPrice += ticketPriceNormal;
            }
        });

        selectedSeatsElement.innerText = seatCount > 0 ? seatCount + ' ghế' : 'Trống';
        totalPriceElement.innerText = totalPrice.toLocaleString('vi-VN');
    }

    seats.forEach(seat => {
        seat.addEventListener('click', () => {
            seat.classList.toggle('selected');
            updateSelection();
        });
    });
});