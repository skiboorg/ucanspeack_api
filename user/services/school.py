from user.models import User
from user.models.school import School


def create_school(admin_user:User):
    School.objects.create(
        name=f'{admin_user.email} school',
        admin=admin_user,
    )


class SchoolService:
    pass
