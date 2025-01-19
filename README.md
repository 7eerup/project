## 백엔드 개발 온보딩 과제

### 레포지토리 저장소 내려받기
```zsh
$ git clone https://github.com/7eerup/project.git
```

### 가상 환경 설정
```zsh
$ python -m venv .venv
$ source .venv/bin/activate
```

### 패키지 설치
```zsh
$ pip install -r requirements.txt
```

### 디렉터리 구조
```
├── django
│   ├── deploy
│       ├── blog
│       ├── project
│       ├── conftest.py
│       ├── db.sqlite3
│       ├── manage.py
│       ├── pytest.ini
│       ├── README.md
│
│   # 백엔드 개발 온보딩 과제 (Python)
├── .gitignore
├── README.md   # 현재 문서
├── requirements.txt    # 패키지 설치
│
│
│   # 관리자 계정 생성
│   # python manage.py createsuperuser
│ 
│   # 서버 실행
│   # python manage.py runserver
│
│   # 로그인 페이지
│   http://127.0.0.1:8000/admin
│
│   # 블로그 리스트 조회
│   http://127.0.0.1:8000/blogs
│
│   # 블로그 게시물 생성
│   http://127.0.0.1:8000/blogs/create
│
│   # 블로그 게시물 수정
│   http://127.0.0.1:8000/blogs/update/post_id/
│   
│   # 블로그 게시물 삭제
│   http://127.0.0.1:8000/blogs/delete/post_id/
│
└── 
```