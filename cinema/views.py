from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import loader
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count

from django.db import models
from .models import Genre, Movie, Cinema, Room, Seat, Showtime, Booking, Ticket, Payment
from .forms import RegisterForm, LoginForm, MovieForm, CinemaForm, ShowtimeForm
from decimal import Decimal
from django.core.paginator import Paginator

# Create your views here.
def health(request):
    return HttpResponse("health")

def index(request):
    movies = Movie.objects.all()
    # Simple partition of movies for home page
    featured_movies = movies[:3] if movies.count() >= 3 else movies
    now_showing_movies = movies
    coming_soon_movies = movies
    return render(request, "home.html", {
        'featured_movies': featured_movies,
        "now_showing_movies": now_showing_movies,
        "coming_soon_movies": coming_soon_movies,
    })

def movie_list_ui(request):
    status = request.GET.get('status', '')
    genre_id = request.GET.get('genre', '')
    query = request.GET.get('q', '')
    
    movies = Movie.objects.all()
    
    if query:
        movies = movies.filter(title__icontains=query)
        
    if genre_id:
        movies = movies.filter(genres__id=genre_id)
        
    if status == 'now_showing':
        movies = movies.filter(showtimes__start_time__gt=timezone.now()).distinct()
    elif status == 'coming_soon':
        movies = movies.exclude(showtimes__start_time__gt=timezone.now()).distinct()
        
    genres = Genre.objects.all()
    return render(request, 'movies/movie_list.html', {
        'movies': movies,
        'status': status,
        'genres': genres
    })

def movie_detail_ui(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    return render(request, "movies/movie_detail.html", {"movie": movie})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    next_url = request.GET.get('next', 'home')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Django users username field for authentication, which stores the email here
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Chào mừng quay trở lại, {user.first_name or user.username}!")
                
                # Safe redirect next URL
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect('home')
            else:
                form.add_error(None, "Email hoặc mật khẩu không chính xác!")
    else:
        form = LoginForm()
    
    return render(request, "account/login.html", {"form": form, "next": next_url})

def user_logout(request):
    logout(request)
    messages.info(request, "Đã đăng xuất tài khoản.")
    return redirect('home')

def user_register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # In our setup, username is the email address
            user = User.objects.create_user(
                username=form.cleaned_data['email'], 
                email=form.cleaned_data['email'], 
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['full_name']
            )
            messages.success(request, "Đăng ký thành công! Vui lòng đăng nhập.")
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, "account/register.html", {"form": form})

def user_forgot_password(request):
    return render(request, 'account/forgot_password.html')

# ==========================================
# LUỒNG ĐẶT VÉ (BOOKING FLOW)
# ==========================================

# Bước 1: Chọn Rạp chiếu của bộ phim đó
def select_cinema(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    
    # Lấy các rạp hiện đang có suất chiếu cho bộ phim này
    # Duyệt qua các Showtime -> Room -> Cinema
    cinemas = Cinema.objects.filter(
        rooms__showtimes__movie=movie,
        rooms__showtimes__start_time__gt=timezone.now()
    ).distinct()
    
    return render(request, 'bookings/select_cinema.html', {
        'movie': movie,
        'cinemas': cinemas
    })

# Bước 2: Chọn suất chiếu tại rạp đã chọn
def select_showtime(request, movie_id, cinema_id):
    movie = get_object_or_404(Movie, id=movie_id)
    cinema = get_object_or_404(Cinema, id=cinema_id)
    
    # Lấy tất cả showtime của bộ phim tại rạp được chọn bắt đầu từ hiện tại
    showtimes = Showtime.objects.filter(
        movie=movie,
        room__cinema=cinema,
        start_time__gt=timezone.now()
    ).order_by('start_time')
    
    # Gom nhóm showtimes theo ngày chiếu
    # Để đơn giản và nhanh chóng, ta có thể phân loại theo Date
    showtimes_by_date = {}
    for showtime in showtimes:
        date_str = showtime.start_time.strftime('%Y-%m-%d')
        if date_str not in showtimes_by_date:
            showtimes_by_date[date_str] = []
        showtimes_by_date[date_str].append(showtime)
        
    # Sắp xếp các ngày
    sorted_dates = sorted(showtimes_by_date.keys())
    showtime_dates = []
    for date_str in sorted_dates:
        # Convert date_str to datetime object to display
        dt = timezone.datetime.strptime(date_str, '%Y-%m-%d')
        showtime_dates.append({
            'date_str': date_str,
            'date_formatted': dt.strftime('%d/%m'),
            'day_name': 'Hôm nay' if dt.date() == timezone.now().date() else dt.strftime('%a'),
            'showtimes': showtimes_by_date[date_str]
        })

    return render(request, 'bookings/select_showtime.html', {
        'movie': movie,
        'cinema': cinema,
        'showtime_dates': showtime_dates
    })

# Bước 3: Chọn ghế ngồi (Yêu cầu Đăng nhập)
@login_required(login_url='login')
def select_seats(request, showtime_id):
    showtime = get_object_or_404(Showtime, id=showtime_id)
    movie = showtime.movie
    room = showtime.room
    cinema = room.cinema
    
    # Lấy danh sách tất cả các ghế của phòng chiếu
    all_seats = Seat.objects.filter(room=room).order_by('row', 'number')
    
    # Lấy danh sách ghế đã được đặt cho suất chiếu này
    # Ghế đã đặt là những ghế thuộc các Ticket của Booking có trạng thái CONFIRMED hoặc PENDING
    booked_tickets = Ticket.objects.filter(
        booking__showtime=showtime,
        booking__status__in=['CONFIRMED', 'PENDING']
    )
    booked_seat_ids = set(ticket.seat_id for ticket in booked_tickets)
    
    # Tổ chức ghế theo hàng (Row) để render bản đồ phòng chiếu
    seats_by_row = {}
    for seat in all_seats:
        if seat.row not in seats_by_row:
            seats_by_row[seat.row] = []
        
        # Thêm thuộc tính động để kiểm tra trạng thái trong template
        seat.is_booked = seat.id in booked_seat_ids
        seat.is_vip = seat.row in ['E', 'F', 'G']  # Hàng E, F, G làm ghế VIP
        seats_by_row[seat.row].append(seat)
        
    if request.method == 'POST':
        # Người dùng gửi danh sách các seat_id được chọn
        selected_seat_ids = request.POST.getlist('selected_seats')
        
        if not selected_seat_ids:
            messages.error(request, "Vui lòng chọn ít nhất một ghế ngồi để tiếp tục!")
            return redirect('select-seats', showtime_id=showtime_id)
            
        try:
            with transaction.atomic():
                # Kiểm tra lại xem có ghế nào vừa bị người khác đặt mất không
                already_booked = Ticket.objects.filter(
                    booking__showtime=showtime,
                    booking__status__in=['CONFIRMED', 'PENDING'],
                    seat_id__in=selected_seat_ids
                ).exists()
                
                if already_booked:
                    messages.error(request, "Một hoặc nhiều ghế bạn chọn vừa được đặt bởi người khác. Vui lòng chọn lại!")
                    return redirect('select-seats', showtime_id=showtime_id)
                
                # Tạo một Booking mới ở trạng thái PENDING
                booking = Booking.objects.create(
                    user=request.user,
                    showtime=showtime,
                    status='PENDING'
                )
                
                # Tạo Ticket tương ứng cho mỗi ghế
                for seat_id in selected_seat_ids:
                    seat = Seat.objects.get(id=seat_id)
                    Ticket.objects.create(
                        booking=booking,
                        seat=seat
                    )
                
                # Tính tổng tiền và chuyển sang trang thanh toán
                # Ghế VIP tăng 20% so với giá cơ bản
                total_amount = 0
                for seat_id in selected_seat_ids:
                    seat = Seat.objects.get(id=seat_id)
                    price = showtime.base_price
                    if seat.row in ['E', 'F', 'G']:
                        price = price * Decimal('1.20')
                    total_amount += price
                
                # Tạo Payment bản nháp
                Payment.objects.create(
                    booking=booking,
                    amount=total_amount,
                    is_successful=False
                )
                
                return redirect('payment', booking_id=booking.id)
                
        except Exception as e:
            messages.error(request, f"Có lỗi xảy ra: {str(e)}")
            return redirect('select-seats', showtime_id=showtime_id)

    return render(request, 'bookings/seat_selection.html', {
        'showtime': showtime,
        'movie': movie,
        'cinema': cinema,
        'room': room,
        'seats_by_row': seats_by_row,
    })

# Bước 4: Thanh toán (Yêu cầu Đăng nhập)
@login_required(login_url='login')
def payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status == 'CONFIRMED':
        return redirect('booking-success', booking_id=booking.id)
    elif booking.status == 'CANCELLED':
        messages.error(request, "Đơn đặt vé này đã bị hủy!")
        return redirect('home')
        
    payment_obj = get_object_or_404(Payment, booking=booking)
    tickets = booking.tickets.all()
    seats_str = ", ".join([f"{t.seat.row}{t.seat.number}" for t in tickets])
    
    if request.method == 'POST':
        # Người dùng nhấn xác nhận thanh toán giả lập
        method = request.POST.get('payment_method', 'BANK_CARD')
        
        try:
            with transaction.atomic():
                # Cập nhật trạng thái Booking
                booking.status = 'CONFIRMED'
                booking.save()
                
                # Cập nhật thông tin Payment
                payment_obj.is_successful = True
                payment_obj.transaction_id = f"LUXE-{booking.id}-{int(timezone.now().timestamp())}"
                payment_obj.paid_at = timezone.now()
                payment_obj.save()
                
                messages.success(request, "Đặt vé thành công! Chúc bạn xem phim vui vẻ.")
                return redirect('booking-success', booking_id=booking.id)
        except Exception as e:
            messages.error(request, f"Thanh toán thất bại: {str(e)}")
            
    return render(request, 'bookings/payment.html', {
        'booking': booking,
        'payment': payment_obj,
        'tickets': tickets,
        'seats_str': seats_str,
    })


# Bước 5: Báo đặt vé thành công (Yêu cầu Đăng nhập)
@login_required(login_url='login')
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user, status='CONFIRMED')
    tickets = booking.tickets.all()
    seats_str = ", ".join([f"{t.seat.row}{t.seat.number}" for t in tickets])
    payment_obj = getattr(booking, 'payment', None)
    
    return render(request, 'bookings/booking_success.html', {
        'booking': booking,
        'tickets': tickets,
        'seats_str': seats_str,
        'payment': payment_obj,
    })

# Trang danh sách vé của tôi
@login_required(login_url='login')
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'account/my_bookings.html', {
        'bookings': bookings
    })

# Trang hồ sơ cá nhân
@login_required(login_url='login')
def user_profile(request):
    user = request.user
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        
        if full_name:
            user.first_name = full_name
        if email and email != user.email:
            if User.objects.filter(email=email).exclude(id=user.id).exists():
                messages.error(request, "Email này đã được sử dụng bởi tài khoản khác.")
                return redirect('profile')
            user.email = email
            user.username = email
        
        user.save()
        messages.success(request, "Cập nhật thông tin cá nhân thành công!")
        return redirect('profile')
        
    return render(request, 'account/profile.html', {'user': user})

@staff_member_required(login_url='login')
def admin_dashboard_ui(request):
    from django.db.models import Sum
    # Statistics
    total_movies = Movie.objects.count()
    today = timezone.now().date()
    total_showtimes = Showtime.objects.filter(start_time__date=today).count()
    total_rooms = Room.objects.count()
    
    total_revenue = Payment.objects.filter(is_successful=True).aggregate(Sum('amount'))['amount__sum'] or 0
    total_tickets_sold = Ticket.objects.filter(booking__status='CONFIRMED').count()
    
    recent_bookings = Booking.objects.all().order_by('-created_at')[:8]

    context = {
        'total_movies': total_movies,
        'total_showtimes': total_showtimes,
        'total_rooms': total_rooms,
        'total_revenue': total_revenue,
        'total_tickets_sold': total_tickets_sold,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'admin/dashboard.html', context)


@staff_member_required(login_url='login')
def admin_bookings(request):
    bookings_list = Booking.objects.all().order_by('-created_at')
    
    # Advanced Filtering
    q = request.GET.get('q', '').strip()
    if q:
        bookings_list = bookings_list.filter(
            models.Q(id__icontains=q) | 
            models.Q(user__username__icontains=q) | 
            models.Q(user__email__icontains=q)
        )
        
    status = request.GET.get('status', '').strip()
    if status:
        bookings_list = bookings_list.filter(status=status)
        
    paginator = Paginator(bookings_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/booking_manage.html', {
        'page_obj': page_obj,
        'status_filter': status,
        'search_query': q
    })

# ==========================================
# QUẢN LÝ PHIM (MOVIE CRUD)
# ==========================================
@staff_member_required(login_url='login')
def admin_movies(request):
    movies_list = Movie.objects.all().order_by('-id')
    
    # Advanced Filtering
    q = request.GET.get('q', '').strip()
    if q:
        movies_list = movies_list.filter(title__icontains=q)
        
    genre_id = request.GET.get('genre', '').strip()
    if genre_id:
        movies_list = movies_list.filter(genres__id=genre_id)
        
    paginator = Paginator(movies_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    genres = Genre.objects.all()
    
    return render(request, 'admin/movie_manage.html', {
        'page_obj': page_obj,
        'genres': genres,
        'selected_genre': genre_id,
        'search_query': q
    })

@staff_member_required(login_url='login')
def admin_movie_create(request):
    form = MovieForm()
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES)
        if form.is_valid():
            movie = form.save()
            messages.success(request, f"Thêm phim '{movie.title}' thành công!")
            return redirect('admin-movies')
            
    return render(request, 'admin/movie_form.html', {
        'form': form,
        'edit_mode': False
    })

@staff_member_required(login_url='login')
def admin_movie_edit(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    if request.method == 'POST':
        form = MovieForm(request.POST, request.FILES, instance=movie)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cập nhật phim '{movie.title}' thành công!")
            return redirect('admin-movies')
    else:
        form = MovieForm(instance=movie)
        
    return render(request, 'admin/movie_form.html', {
        'form': form,
        'movie': movie,
        'edit_mode': True
    })

@staff_member_required(login_url='login')
def admin_movie_delete(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    title = movie.title
    movie.delete()
    messages.success(request, f"Đã xóa phim '{title}' thành công!")
    return redirect('admin-movies')


# ==========================================
# QUẢN LÝ RẠP CHIẾU (CINEMA CRUD)
# ==========================================
@staff_member_required(login_url='login')
def admin_cinemas(request):
    cinemas_list = Cinema.objects.all().order_by('-id')
    
    # Advanced Filtering
    q = request.GET.get('q', '').strip()
    if q:
        cinemas_list = cinemas_list.filter(
            models.Q(name__icontains=q) | 
            models.Q(location__icontains=q)
        )
        
    paginator = Paginator(cinemas_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'admin/cinema_manage.html', {
        'page_obj': page_obj,
        'search_query': q
    })

@staff_member_required(login_url='login')
def admin_cinema_create(request):
    form = CinemaForm()
    if request.method == 'POST':
        form = CinemaForm(request.POST, request.FILES)
        if form.is_valid():
            cinema = form.save()
            messages.success(request, f"Thêm rạp '{cinema.name}' thành công!")
            return redirect('admin-cinemas')
            
    return render(request, 'admin/cinema_form.html', {
        'form': form,
        'edit_mode': False
    })

@staff_member_required(login_url='login')
def admin_cinema_edit(request, cinema_id):
    cinema = get_object_or_404(Cinema, id=cinema_id)
    if request.method == 'POST':
        form = CinemaForm(request.POST, request.FILES, instance=cinema)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cập nhật rạp '{cinema.name}' thành công!")
            return redirect('admin-cinemas')
    else:
        form = CinemaForm(instance=cinema)
        
    return render(request, 'admin/cinema_form.html', {
        'form': form,
        'cinema': cinema,
        'edit_mode': True
    })

@staff_member_required(login_url='login')
def admin_cinema_delete(request, cinema_id):
    cinema = get_object_or_404(Cinema, id=cinema_id)
    name = cinema.name
    cinema.delete()
    messages.success(request, f"Đã xóa rạp '{name}' thành công!")
    return redirect('admin-cinemas')


# ==========================================
# QUẢN LÝ LỊCH CHIẾU (SHOWTIME CRUD)
# ==========================================
@staff_member_required(login_url='login')
def admin_showtimes(request):
    showtimes_list = Showtime.objects.all().order_by('-start_time')
    
    # Advanced Filtering
    movie_id = request.GET.get('movie', '').strip()
    if movie_id:
        showtimes_list = showtimes_list.filter(movie__id=movie_id)
        
    cinema_id = request.GET.get('cinema', '').strip()
    if cinema_id:
        showtimes_list = showtimes_list.filter(room__cinema__id=cinema_id)
        
    paginator = Paginator(showtimes_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    movies = Movie.objects.all()
    cinemas = Cinema.objects.all()
    
    return render(request, 'admin/showtime_manage.html', {
        'page_obj': page_obj,
        'movies': movies,
        'cinemas': cinemas,
        'selected_movie': movie_id,
        'selected_cinema': cinema_id
    })

@staff_member_required(login_url='login')
def admin_showtime_create(request):
    form = ShowtimeForm()
    if request.method == 'POST':
        form = ShowtimeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thêm suất chiếu mới thành công!")
            return redirect('admin-showtimes')
            
    return render(request, 'admin/showtime_form.html', {
        'form': form,
        'edit_mode': False
    })

@staff_member_required(login_url='login')
def admin_showtime_edit(request, showtime_id):
    showtime = get_object_or_404(Showtime, id=showtime_id)
    if request.method == 'POST':
        form = ShowtimeForm(request.POST, instance=showtime)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật suất chiếu thành công!")
            return redirect('admin-showtimes')
    else:
        form = ShowtimeForm(instance=showtime)
        
    return render(request, 'admin/showtime_form.html', {
        'form': form,
        'showtime': showtime,
        'edit_mode': True
    })

@staff_member_required(login_url='login')
def admin_showtime_delete(request, showtime_id):
    showtime = get_object_or_404(Showtime, id=showtime_id)
    showtime.delete()
    messages.success(request, "Đã xóa suất chiếu thành công!")
    return redirect('admin-showtimes')