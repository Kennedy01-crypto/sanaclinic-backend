from django.test import SimpleTestCase
from django.urls import reverse


class ApiRootViewTests(SimpleTestCase):
    def test_root_landing_page_links_to_backend_resources(self):
        response = self.client.get(reverse("api-root"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html; charset=utf-8")
        self.assertContains(response, "SanaClinic")
        self.assertContains(response, 'href="/admin/"')
        self.assertContains(response, 'href="/api/docs/"')
        self.assertContains(response, 'href="/api/schema/"')

    def test_production_frontend_origin_is_allowed_for_cors(self):
        response = self.client.options(
            "/api/accounts/me/",
            HTTP_ORIGIN="https://sanaclinic-frontend.vercel.app",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="GET",
        )

        self.assertEqual(
            response["Access-Control-Allow-Origin"],
            "https://sanaclinic-frontend.vercel.app",
        )
        self.assertEqual(response["Access-Control-Allow-Credentials"], "true")
