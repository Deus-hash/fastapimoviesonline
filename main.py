from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import Movietop
import os
import shutil
import json
from datetime import datetime, timedelta
from typing import Optional
import jwt

app = FastAPI()

SECRET_KEY = "secretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 2

security = HTTPBearer()

movie_top_10 = [
    Movietop(name="Всеведущий читатель", id=1, cost=23, director="Ким Бён-у"),
    Movietop(name="Пятый элемент", id=2, cost=90, director="Люк Бессон"),
    Movietop(name="Точка ноль", id=3, cost=5, director="Сергей Пикалов"),
    Movietop(name="Министерство неджентльменских дел", id=4, cost=60, director="Гай Ричи"),
    Movietop(name="Мстители: Война бесконечности", id=5, cost=321, director="Энтони и Джо Руссо"),
    Movietop(name="Достать ножи", id=6, cost=40, director="Райан Джонсон"),
    Movietop(name="Король Лев", id=7, cost=45, director="Джон Фавро"),
    Movietop(name="Майор Гром", id=8, cost=5, director="Олег Трофим"),
    Movietop(name="Тихое место", id=9, cost=19, director="Джон Красински"),
    Movietop(name="Сто лет тому вперёд", id=10, cost=150, director="Александр Андрющенко")
]

USERS = {
    "admin": "password",
    "user": "pass"
}

MOVIES_FILE = "movies.json"
USERS_FILE = "users.json"


def get_movies():
    if os.path.exists(MOVIES_FILE):
        with open(MOVIES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_movies(movies):
    with open(MOVIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)


def get_next_id():
    movies = get_movies()
    if not movies:
        return 1
    return max(movie['id'] for movie in movies) + 1


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(payload: dict = Depends(verify_token)):
    username = payload.get("sub")
    if username not in USERS:
        raise HTTPException(status_code=401, detail="User not found")
    return username


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    public_routes = ["/login", "/login-form", "/study", "/movietop", "/static", "/api/login"]
    if any(request.url.path.startswith(route) for route in public_routes) or request.url.path == "/":
        response = await call_next(request)
        return response

    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            request.state.user = payload.get("sub")
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            if request.url.path.startswith("/api/"):
                return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
            else:
                response = RedirectResponse(url="/login")
                response.delete_cookie("access_token")
                return response
    else:
        if request.url.path.startswith("/api/"):
            return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
        else:
            return RedirectResponse(url="/login")

    response = await call_next(request)
    return response


os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

DARK_THEME_STYLE = """
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            background-color: #1a1a1a; 
            color: #e0e0e0; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
        }
        h1, h2, h3 { 
            color: #ffffff; 
        }
        a { 
            color: #4dabf7; 
            text-decoration: none; 
        }
        a:hover { 
            color: #74c0fc; 
            text-decoration: underline; 
        }
        .card { 
            background-color: #2d2d2d; 
            border: 1px solid #404040; 
            border-radius: 8px; 
            padding: 20px; 
            margin: 15px 0; 
        }
        .movie-card { 
            display: flex; 
            gap: 20px; 
            background-color: #2d2d2d; 
            border: 1px solid #404040; 
            border-radius: 8px; 
            padding: 20px; 
            margin: 15px 0; 
        }
        .btn { 
            background: #1971c2; 
            color: white; 
            padding: 10px 20px; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            text-decoration: none; 
            display: inline-block; 
            margin: 5px; 
        }
        .btn:hover { 
            background: #1864ab; 
        }
        .btn-success { 
            background: #2b8a3e; 
        }
        .btn-success:hover { 
            background: #2f9e44; 
        }
        .btn-danger { 
            background: #e03131; 
        }
        .btn-danger:hover { 
            background: #c92a2a; 
        }
        input, textarea, select { 
            width: 100%; 
            padding: 10px; 
            border: 1px solid #404040; 
            border-radius: 6px; 
            background-color: #2d2d2d; 
            color: #e0e0e0; 
            box-sizing: border-box; 
            margin-bottom: 10px; 
        }
        input:focus, textarea:focus { 
            border-color: #1971c2; 
            outline: none; 
        }
        .form-group { 
            margin-bottom: 20px; 
        }
        label { 
            display: block; 
            margin-bottom: 8px; 
            font-weight: bold; 
            color: #ffffff; 
        }
        .checkbox { 
            width: auto; 
            margin-right: 10px; 
        }
        img { 
            border-radius: 6px; 
        }
        .error { 
            color: #ff6b6b; 
            background: #2d1a1a; 
            padding: 10px; 
            border-radius: 6px; 
            margin: 10px 0; 
            display: none; 
        }
        .success { 
            color: #51cf66; 
            background: #1a2d1a; 
            padding: 10px; 
            border-radius: 6px; 
            margin: 10px 0; 
        }
        .user-info { 
            background: #1a2d2d; 
            padding: 10px; 
            border-radius: 6px; 
            margin: 10px 0; 
        }
        .nav { 
            display: flex; 
            gap: 10px; 
            margin: 20px 0; 
            flex-wrap: wrap; 
        }
    </style>
"""


@app.get("/")
async def root_page(request: Request):
    user = getattr(request.state, 'user', None)

    if user:
        return HTMLResponse(f"""
        <html>
        <head>
            <title>Главная</title>
            {DARK_THEME_STYLE}
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h1>Добро пожаловать, {user}!</h1>
                    <p>Вы успешно авторизованы в системе управления фильмами.</p>

                    <div class="nav">
                        <a href="/user-page" class="btn btn-success">Личный кабинет</a>
                        <a href="/add-movie-form" class="btn">Добавить фильм</a>
                        <a href="/movies" class="btn">Все фильмы</a>
                        <a href="/movietop" class="btn">Топ-10 фильмов</a>
                        <a href="/study/page" class="btn">Об университете</a>
                        <a href="/logout" class="btn btn-danger">Выйти</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """)
    else:
        return HTMLResponse(f"""
        <html>
        <head>
            <title>Главная</title>
            {DARK_THEME_STYLE}
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h1>Система управления фильмами</h1>
                    <p>Для доступа к функциям системы необходимо авторизоваться.</p>

                    <div class="nav">
                        <a href="/login" class="btn btn-success">Войти в систему</a>
                        <a href="/study" class="btn">Об университете</a>
                        <a href="/movietop" class="btn">Топ-10 фильмов</a>
                    </div>

                    <div class="card">
                        <h3>Тестовые учетные записи:</h3>
                        <ul>
                            <li><strong>admin</strong> / password</li>
                            <li><strong>user</strong> / pass</li>
                        </ul>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """)


@app.get("/study")
async def study_info():
    return {
        "university": "Брянский государственный инженерно-технологический университет",
        "photo_url": "/static/SUx182_2x.jpg"
    }


@app.get("/study/page", response_class=HTMLResponse)
async def study_page():
    return f"""
    <html>
        <head>
            <title>Университет</title>
            {DARK_THEME_STYLE}
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h1>Брянский государственный инженерно-технологический университет</h1>
                    <img src="/static/SUx182_2x.jpg" alt="Университет" style="max-width: 500px; height: auto;">
                    <div class="nav">
                        <a href="/" class="btn">На главную</a>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """


@app.get("/movietop/{movie_name}")
async def get_movie_info(movie_name: str):
    movie = next((m for m in movie_top_10 if m.name.lower() == movie_name.lower()), None)
    if movie:
        return movie
    raise HTTPException(status_code=404, detail="Movie not found")


@app.get("/movietop/")
async def get_all_movies():
    return {"movies": movie_top_10}


@app.get("/movietop", response_class=HTMLResponse)
async def get_all_movies_page():
    movies_html = ""
    for movie in movie_top_10:
        movies_html += f"""
        <div class="movie-card">
            <div style="flex-grow: 1;">
                <h2>{movie.name}</h2>
                <p><strong>Режиссер:</strong> {movie.director}</p>
                <p><strong>Бюджет:</strong> ${movie.cost} млн</p>
                <p><strong>ID:</strong> {movie.id}</p>
            </div>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>Топ-10 фильмов</title>
        {DARK_THEME_STYLE}
    </head>
    <body>
        <div class="container">
            <h1>Топ-10 фильмов</h1>
            <div class="nav">
                <a href="/" class="btn">На главную</a>
            </div>
            {movies_html}
        </div>
    </body>
    </html>
    """


@app.post("/api/login")
async def login_json(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    if username not in USERS or USERS[username] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@app.post("/login-form")
async def login_form(
        username: str = Form(...),
        password: str = Form(...)
):
    if username not in USERS or USERS[username] != password:
        return HTMLResponse(f"""
        <html>
        <head>
            <title>Ошибка входа</title>
            {DARK_THEME_STYLE}
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h1>Ошибка входа</h1>
                    <div class="error" style="display: block;">
                        Неверное имя пользователя или пароль
                    </div>
                    <div class="nav">
                        <a href="/login" class="btn">Вернуться к входу</a>
                        <a href="/" class="btn">На главную</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )

    response = RedirectResponse(url="/user-page", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return response


@app.get("/login", response_class=HTMLResponse)
async def login_form_page():
    return f"""
    <html>
    <head>
        <title>Вход в систему</title>
        {DARK_THEME_STYLE}
        <script>
            function handleLogin(event) {{
                event.preventDefault();

                const formData = new FormData(event.target);
                const submitBtn = event.target.querySelector('button[type="submit"]');
                submitBtn.textContent = 'Вход...';
                submitBtn.disabled = true;

                fetch('/login-form', {{
                    method: 'POST',
                    body: formData
                }})
                .then(response => {{
                    if (response.redirected) {{
                        window.location.href = response.url;
                    }} else {{
                        return response.json().then(data => {{
                            throw new Error(data.detail || 'Ошибка входа');
                        }});
                    }}
                }})
                .catch(error => {{
                    const errorDiv = document.getElementById('error-message');
                    errorDiv.textContent = error.message;
                    errorDiv.style.display = 'block';

                    submitBtn.textContent = 'Войти';
                    submitBtn.disabled = false;
                }});
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>Вход в систему</h1>

                <div id="error-message" class="error" style="display: none;"></div>

                <form onsubmit="handleLogin(event)">
                    <div class="form-group">
                        <label>Имя пользователя:</label>
                        <input type="text" name="username" required>
                    </div>
                    <div class="form-group">
                        <label>Пароль:</label>
                        <input type="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-success">Войти</button>
                </form>

                <br>
                <p><strong>Тестовые пользователи:</strong></p>
                <ul>
                    <li>admin / password</li>
                    <li>user / pass</li>
                </ul>
                <div class="nav">
                    <a href="/" class="btn">На главную</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/user-page", response_class=HTMLResponse)
async def user_page(request: Request):
    user = getattr(request.state, 'user', None)
    if not user:
        return RedirectResponse(url="/login")

    all_movies = get_movies()
    top_movies_data = [movie.model_dump() for movie in movie_top_10]

    return f"""
    <html>
    <head>
        <title>Личный кабинет</title>
        {DARK_THEME_STYLE}
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>Добро пожаловать, {user}!</h1>
                <div class="success">
                    Вы успешно авторизованы! Токен автоматически сохранен в cookies.
                </div>

                <div class="user-info">
                    <h3>Статистика:</h3>
                    <p><strong>Имя пользователя:</strong> {user}</p>
                    <p><strong>Всего фильмов в базе:</strong> {len(all_movies)}</p>
                    <p><strong>Топ-10 фильмов:</strong> {len(top_movies_data)}</p>
                    <p><strong>Срок действия сессии:</strong> {ACCESS_TOKEN_EXPIRE_MINUTES} минут</p>
                </div>

                <h2>Доступные действия:</h2>
                <div class="nav">
                    <a href="/add-movie-form" class="btn btn-success">Добавить фильм</a>
                    <a href="/movies" class="btn">Все фильмы</a>
                    <a href="/movietop" class="btn">Топ-10 фильмов</a>
                    <a href="/" class="btn">На главную</a>
                    <a href="/logout" class="btn btn-danger">Выйти</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/user")
async def user_info_api(current_user: str = Depends(get_current_user)):
    all_movies = get_movies()
    top_movies_data = [movie.model_dump() for movie in movie_top_10]

    user_data = {
        "username": current_user,
        "movies": {
            "top_10": top_movies_data,
            "custom_movies": all_movies
        }
    }

    return user_data


@app.get("/add-movie-form", response_class=HTMLResponse)
async def add_movie_form(request: Request):
    user = getattr(request.state, 'user', None)
    if not user:
        return RedirectResponse(url="/login")

    return f"""
    <html>
    <head>
        <title>Добавить фильм</title>
        {DARK_THEME_STYLE}
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>Добавить новый фильм</h1>
                <p>Вы вошли как: <strong>{user}</strong></p>
                <form action="/add-movie" method="post" enctype="multipart/form-data">
                    <div class="form-group">
                        <label>Название фильма:</label>
                        <input type="text" name="title" required>
                    </div>
                    <div class="form-group">
                        <label>Режиссер:</label>
                        <input type="text" name="director" required>
                    </div>
                    <div class="form-group">
                        <label>Год выпуска:</label>
                        <input type="number" name="year" required>
                    </div>
                    <div class="form-group">
                        <label>Бюджет (в млн $):</label>
                        <input type="number" name="budget" required>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" name="oscar" value="true" class="checkbox">
                            Получил Оскар
                        </label>
                    </div>
                    <div class="form-group">
                        <label>Описание фильма:</label>
                        <textarea name="description" rows="4" placeholder="Введите описание фильма..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Обложка фильма:</label>
                        <input type="file" name="poster" accept="image/*" required>
                    </div>
                    <button type="submit" class="btn btn-success">Добавить фильм</button>
                </form>
                <div class="nav">
                    <a href="/movies" class="btn">Посмотреть все фильмы</a>
                    <a href="/user-page" class="btn">Личный кабинет</a>
                    <a href="/" class="btn">На главную</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@app.post("/add-movie")
async def add_movie(
        request: Request,
        title: str = Form(...),
        director: str = Form(...),
        year: int = Form(...),
        budget: int = Form(...),
        oscar: bool = Form(False),
        description: str = Form(""),
        poster: UploadFile = File(...)
):
    user = getattr(request.state, 'user', None)
    if not user:
        return RedirectResponse(url="/login")

    movies = get_movies()
    next_id = get_next_id()

    poster_filename = f"poster_{next_id}.jpg"
    poster_path = f"static/{poster_filename}"

    with open(poster_path, "wb") as buffer:
        shutil.copyfileobj(poster.file, buffer)

    movie_data = {
        "id": next_id,
        "title": title,
        "director": director,
        "year": year,
        "budget": budget,
        "oscar": oscar,
        "description": description,
        "posterurl": f"/static/{poster_filename}",
        "added_by": user,
        "added_at": datetime.now().isoformat()
    }

    movies.append(movie_data)
    save_movies(movies)

    return RedirectResponse(url="/movies", status_code=303)


@app.get("/movies", response_class=HTMLResponse)
async def get_all_movies_page(request: Request):
    user = getattr(request.state, 'user', None)
    if not user:
        return RedirectResponse(url="/login")

    movies = get_movies()

    if not movies:
        return f"""
        <html>
            <head>
                <title>Фильмы</title>
                {DARK_THEME_STYLE}
            </head>
            <body>
                <div class="container">
                    <div class="card">
                        <h1>Добавленные фильмы</h1>
                        <p>Пока нет добавленных фильмов.</p>
                        <div class="nav">
                            <a href="/add-movie-form" class="btn btn-success">Добавить первый фильм</a>
                            <a href="/user-page" class="btn">Личный кабинет</a>
                            <a href="/" class="btn">На главную</a>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """

    movies_html = ""
    for movie in movies:
        oscar = "🏆" if movie["oscar"] else ""
        added_by = movie.get("added_by", "unknown")
        movies_html += f"""
        <div class="movie-card">
            <img src="{movie['posterurl']}" alt="{movie['title']}" style="width: 120px; height: 180px; object-fit: cover;">
            <div style="flex-grow: 1;">
                <h2>{movie['title']} {oscar}</h2>
                <p><strong>Режиссер:</strong> {movie['director']}</p>
                <p><strong>Год:</strong> {movie['year']}</p>
                <p><strong>Бюджет:</strong> ${movie['budget']} млн</p>
                <p><strong>Оскар:</strong> {'Да' if movie['oscar'] else 'Нет'}</p>
                <p><strong>Описание:</strong> {movie['description'] or 'Нет описания'}</p>
                <p><strong>ID:</strong> {movie['id']}</p>
                <p><strong>Добавлено пользователем:</strong> {added_by}</p>
            </div>
        </div>
        """

    return f"""
    <html>
    <head>
        <title>Добавленные фильмы</title>
        {DARK_THEME_STYLE}
    </head>
    <body>
        <div class="container">
            <h1>Все добавленные фильмы</h1>
            <div class="nav">
                <a href="/add-movie-form" class="btn btn-success">Добавить фильм</a>
                <a href="/user-page" class="btn">Личный кабинет</a>
                <a href="/" class="btn">На главную</a>
            </div>
            {movies_html}
        </div>
    </body>
    </html>
    """

@app.get("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return RedirectResponse(url="/login")


@app.get("/verify-token")
async def verify_token_endpoint(current_user: str = Depends(get_current_user)):
    return {"message": "Token is valid", "username": current_user}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", port=8168, reload=True)