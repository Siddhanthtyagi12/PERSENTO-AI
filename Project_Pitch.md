0# Vidyalaya AI: Cloud-Native School Attendance Solution
*Prepared by ___SIDDHANTH TYAGI__*

## 1. Introduction
Modern schools require scalable, professional solutions. **Vidyalaya AI** is a production-ready **Cloud-Native SaaS (Software as a Service)** platform that uses high-accuracy Facial Recognition to automate attendance, provide real-time analytics to parents/principals, and eliminate proxy attendance forever.

## 2. Advanced Technology & Architecture
Our system has evolved from a local prototype into a massive **Cloud-Scale Infrastructure**:
1. **Cloud-Native Backend**: Deployed on **Render PaaS (Linux)**. The backend and API have been unified to serve both the web dashboard and mobile app concurrently.
2. **SaaS Multi-Tenancy**: Built with a "Multi-Tenant" architecture, allowing multiple schools to register and manage their own local data independently on one central platform.
3. **AI Core (MediaPipe Tasks)**: Uses Google’s latest **MediaPipe Face Mesh (478-point)** CNN model. It captures 30-sample biometric signatures during registration to ensure 99.9% accuracy.
4. **Cloud Database (Supabase)**: Migrated from SQLite to **PostgreSQL on Supabase Cloud**. This ensures data is permanent, secure, and accessible 24/7 from anywhere in the world.

## 3. Top Features (Hackathon Highlights)
- **Hybrid Deployment**: Local camera monitoring synced with Cloud Analytics.
- **Cross-Platform Mobility**: An integrated **React Native Mobile App** allows teachers to mark attendance on the go, with data reflecting on the principal's cloud dashboard instantly.
- **Anti-Spoofing (Liveness)**: Built-in liveness detection prevents spoofing via photos or digital screens.
- **Automated Absence Alerts**: Integarted with **Twilio API** to send instant SMS/WhatsApp alerts to parents when a child is absent.
- **Data Privacy**: No raw images are stored. Only normalized 128-dimensional biometric vectors are encrypted and stored in the cloud.
- **Professional Analytics**: Dashboard features attendance trends, critical student lists (low attendance alerts), and one-click PDF/Excel export modules.
- **Smart AI Quiz Generator**: A game-changing feature for teachers. Using **Google Gemini 1.5/2.0**, teachers can paste lesson notes and generate professional Multiple Choice Questions (MCQs) in seconds, drastically reducing administrative workload.

## 4. Technical Stack
- **AI/ML**: Google MediaPipe (Face Mesh), Google Gemini AI (LLM), NumPy, OpenCV.
- **Cloud Hosting**: Render (Backend), Supabase (Database).
- **Backend Framework**: Python Flask (Gunicorn WSGI).
- **Communication**: Twilio SMS API.
- **Mobile**: React Native / Expo (Android/iOS).
- **Frontend**: HTML5, Tailwind CSS, Lucide Icons.

## 5. Vision: The Future of School Security
Vidyalaya AI is not just an attendance logger; it is a security hub. Future updates include **Bus Tracking integration**, **Automated Gate Barriers**, and **AI Behavior Analysis** to detect student distress or unusual activity.
