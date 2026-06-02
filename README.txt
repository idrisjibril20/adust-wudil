=======================================================
  ALIKO DANGOTE UNIVERSITY OF SCIENCE AND TECHNOLOGY
  WUDIL - CAMPUS MANAGEMENT SYSTEM (ADUST)
=======================================================

RUNNING LOCALLY
---------------
1. Open Command Prompt in this folder
2. Run: pip install flask werkzeug
3. Run: python app.py
4. Open browser: http://localhost:5000

LOGIN DETAILS (Local)
---------------------
Admin:    admin@adust.edu.ng    / admin123
Staff:    staff@adust.edu.ng    / staff123
Student:  student@adust.edu.ng  / student123
Security: security@adust.edu.ng / security123

DEPLOYING TO RAILWAY (Online)
------------------------------
Step 1: Install Git from https://git-scm.com/downloads
Step 2: Create free account at https://github.com
Step 3: Create free account at https://railway.app (sign up with GitHub)

Step 4: Open Command Prompt in this folder and run:
   git init
   git add .
   git commit -m "ADUST Wudil first deploy"

Step 5: Go to github.com, click New Repository
   - Name it: adust-wudil
   - Click Create Repository
   - Copy and run the commands GitHub shows you

Step 6: Go to railway.app
   - Click New Project
   - Click Deploy from GitHub repo
   - Select adust-wudil
   - Wait 2 minutes for deployment

Step 7: In Railway click Settings > Networking > Generate Domain
   - You will get a public URL like: https://adust-wudil.railway.app
   - Share this with students and staff!

FEATURES
--------
- Vehicle Registration and Approval
- Digital Sticker Code Generation
- Gate Entry/Exit Logging
- Task Management (Kanban Board)
- User Role Management (Admin/Staff/Student/Security)
- In-app Notifications

PROJECT STRUCTURE
-----------------
adust-wudil/
├── app.py              <- Flask backend
├── Procfile            <- Railway start command
├── requirements.txt    <- Python packages
├── runtime.txt         <- Python version
├── railway.json        <- Railway config
├── templates/          <- HTML pages (10 files)
└── static/
    ├── css/main.css    <- Stylesheet
    └── js/main.js      <- JavaScript

=======================================================
  Built for Aliko Dangote University of Science
  and Technology Wudil - Campus Operations
=======================================================
