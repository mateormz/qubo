<h1 align="center">🧠 QUBO — App para Aprender Matemática Jugando</h1>

QUBO es una plataforma educativa gamificada que permite a estudiantes de secundaria practicar matemáticas a través de minijuegos, desafíos diarios y una mascota virtual personalizable. También ofrece a los profesores herramientas para asignar actividades, monitorear el avance y dar retroalimentación individual.

---

## 🚀 Características Principales

### 👨‍🏫 Vista del Profesor
- Registro e inicio de sesión con rol docente.
- Gestión de salones y estudiantes.
- Asignación de minijuegos y actividades matemáticas.
- Visualización de progreso individual.
- Panel de estadísticas, logros y puntos acumulados.

### 👦 Vista del Estudiante
- Registro mediante código de clase.
- Mascota virtual personalizable (ropa, color, accesorios).
- Minijuegos y quizzes matemáticos alineados al currículo escolar.
- Retos diarios, sistema de puntos y logros desbloqueables.
- Tienda virtual para canjear monedas “qu”.
- Chatbot de ayuda.

---

## 🧱 Tech Stack

### 🔹 Frontend
- React.js
- HTML5, CSS3, JavaScript
- React Router DOM
- Context API
- Tailwind CSS o Material UI

### 🔹 Backend (Serverless)
- AWS Lambda (funciones backend)
- API Gateway (exposición de endpoints)
- DynamoDB (base de datos NoSQL)
- JWT para autenticación y autorización
- CloudWatch (logs y métricas)

### 🔹 Infraestructura
- Amazon S3 (hosting del frontend)
- CloudFront (distribución global)
- GitHub (control de versiones y CI/CD)
- Docker (desarrollo y testing local)

---

## 📦 Estructura del Proyecto
- /frontend --> App en React
- /backend --> Funciones Lambda (JavaScript)
- /infrastructure --> Configuraciones de AWS (Serverless Framework o SAM)
- /docs --> Documentación de endpoints, modelos y flujos
- /assets --> Imágenes, logo, íconos
