"""
URL configuration for clinic_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def api_root_view(request):
    return HttpResponse(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f5f8f6">
  <title>SanaClinic | Backend</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #18332d;
      background: #f5f8f6;
      font-synthesis: none;
      text-rendering: optimizeLegibility;
    }
    * { box-sizing: border-box; }
    body {
      min-height: 100vh;
      margin: 0;
      display: grid;
      place-items: center;
      padding: 40px 20px;
      background:
        radial-gradient(ellipse at 80% 5%, rgba(167, 220, 196, .35), transparent 35%),
        #f5f8f6;
    }
    main { width: min(100%, 860px); }
    .brand {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      color: #19745d;
      font-size: .82rem;
      font-weight: 750;
      letter-spacing: .13em;
      text-transform: uppercase;
    }
    .brand-mark {
      display: grid;
      width: 34px;
      height: 34px;
      place-items: center;
      border-radius: 11px;
      background: #19745d;
      color: white;
      font-size: 1.05rem;
      letter-spacing: 0;
    }
    .hero { padding: 42px 0 30px; }
    .status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 19px;
      padding: 7px 11px;
      border: 1px solid #cce6d8;
      border-radius: 999px;
      background: #edf8f1;
      color: #286947;
      font-size: .8rem;
      font-weight: 650;
    }
    .status::before {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #36a269;
      content: "";
    }
    h1 {
      max-width: 650px;
      margin: 0;
      font-size: clamp(2.35rem, 6vw, 4rem);
      letter-spacing: -.055em;
      line-height: 1.04;
    }
    .intro {
      max-width: 620px;
      margin: 18px 0 0;
      color: #61746e;
      font-size: 1.08rem;
      line-height: 1.7;
    }
    .section-heading {
      margin: 15px 0 14px;
      color: #536860;
      font-size: .78rem;
      font-weight: 750;
      letter-spacing: .12em;
      text-transform: uppercase;
    }
    .links {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
    }
    .card {
      display: flex;
      min-height: 176px;
      flex-direction: column;
      padding: 21px;
      border: 1px solid #e0e9e4;
      border-radius: 16px;
      background: rgba(255, 255, 255, .88);
      color: inherit;
      text-decoration: none;
      box-shadow: 0 8px 24px rgba(26, 63, 49, .035);
      transition: border-color .18s ease, transform .18s ease, box-shadow .18s ease;
    }
    .card:hover, .card:focus-visible {
      transform: translateY(-3px);
      border-color: #86c5a6;
      box-shadow: 0 14px 32px rgba(26, 63, 49, .09);
    }
    .card:focus-visible { outline: 3px solid #7abf9e; outline-offset: 3px; }
    .icon {
      display: grid;
      width: 38px;
      height: 38px;
      place-items: center;
      margin-bottom: 18px;
      border-radius: 11px;
      background: #eaf5ef;
      color: #19745d;
      font-size: 1.05rem;
      font-weight: 750;
    }
    .card strong { font-size: 1rem; }
    .card span:last-child {
      margin-top: 7px;
      color: #71817b;
      font-size: .88rem;
      line-height: 1.5;
    }
    footer {
      margin-top: 28px;
      padding-top: 17px;
      border-top: 1px solid #e0e9e4;
      color: #84938d;
      font-size: .82rem;
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; }
    }
  </style>
</head>
<body>
  <main>
    <div class="brand"><span class="brand-mark" aria-hidden="true">S</span> SanaClinic</div>
    <section class="hero" aria-labelledby="page-title">
      <div class="status">Backend API online</div>
      <h1 id="page-title">Clinic appointments, made simpler.</h1>
      <p class="intro">
        Welcome to the SanaClinic backend. Explore the API documentation or open the
        administration tools using the links below.
      </p>
    </section>
    <section aria-labelledby="explore-heading">
      <h2 class="section-heading" id="explore-heading">Explore the backend</h2>
      <nav class="links" aria-label="Backend resources">
        <a class="card" href="/admin/">
          <span class="icon" aria-hidden="true">A</span>
          <strong>Django Admin</strong>
          <span>Manage clinic data and administration. Staff sign-in required.</span>
        </a>
        <a class="card" href="/api/docs/">
          <span class="icon" aria-hidden="true">↗</span>
          <strong>Swagger UI</strong>
          <span>Browse API operations and try authenticated requests.</span>
        </a>
        <a class="card" href="/api/schema/">
          <span class="icon" aria-hidden="true">{ }</span>
          <strong>OpenAPI Schema</strong>
          <span>View or download the machine-readable API specification.</span>
        </a>
      </nav>
    </section>
    <footer>SanaClinic Backend · Django REST Framework</footer>
  </main>
</body>
</html>""",
        content_type="text/html; charset=utf-8",
    )


urlpatterns = [
    path('', api_root_view, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/accounts/', include('accounts.urls')),
    path('api/doctors/', include('doctors.urls')),
    path('api/appointments/', include('appointments.urls')),
]
