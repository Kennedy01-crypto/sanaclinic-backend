from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations, models
from django.db.models import F, Func, Q


class Migration(migrations.Migration):

    dependencies = [
        ("appointments", "0001_initial"),
    ]

    operations = [
        BtreeGistExtension(),
        migrations.AddConstraint(
            model_name="appointment",
            constraint=ExclusionConstraint(
                name="no_overlapping_booked_doctor_appointments",
                expressions=[
                    (F("doctor"), RangeOperators.EQUAL),
                    (
                        Func(
                            F("start_at"),
                            F("end_at"),
                            function="TSTZRANGE",
                            output_field=DateTimeRangeField(),
                        ),
                        RangeOperators.OVERLAPS,
                    ),
                ],
                condition=Q(status="booked"),
            ),
        ),
        migrations.AddConstraint(
            model_name="appointment",
            constraint=ExclusionConstraint(
                name="no_overlapping_booked_patient_appointments",
                expressions=[
                    (F("patient"), RangeOperators.EQUAL),
                    (
                        Func(
                            F("start_at"),
                            F("end_at"),
                            function="TSTZRANGE",
                            output_field=DateTimeRangeField(),
                        ),
                        RangeOperators.OVERLAPS,
                    ),
                ],
                condition=Q(status="booked"),
            ),
        ),
    ]
