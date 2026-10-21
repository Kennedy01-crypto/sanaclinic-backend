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
