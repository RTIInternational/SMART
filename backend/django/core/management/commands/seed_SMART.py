from django.core.management.base import BaseCommand
from django.db import transaction
from core.management.commands.seed_lib.seed_users import seed_users
from core.management.commands.seed_lib.seed_projects import seed_project
from core.management.commands.seed_lib.label_project import label_project


class Command(BaseCommand):
    help = "Seeds the SMART App with a few users, projects, and labels"

    def handle(self, *args, **options):
        print("Seeding the database with some test data...")
        with transaction.atomic():
            print("Seeding users...")
            root_profile, tom_profile, jade_profile = seed_users()

            print("Seeding projects...")
            root_project = seed_project(
                creator=root_profile,
                name="Root Only Project",
                description="This is a project for only the root user. The root user is the creator.  This project's data file has labels.",
                data_file="./core/data/test_files/test_some_labels.csv",
                label_list=["about cats", "not about cats", "unclear"],
                perm_list=[],
                classifier="logistic regression",
            )
            multi_user_project = seed_project(
                creator=root_profile,
                name="Three User Project",
                description="This is a project that is coded by three different users.  No labels were in the data file to begin with.",
                data_file="./core/data/test_files/test_no_labels.csv",
                label_list=["about cats", "not about cats", "unclear"],
                perm_list=[tom_profile, jade_profile],
                classifier="logistic regression",
            )
            seed_project(
                creator=root_profile,
                name="No Label Project",
                description="This project has no labels, all charts should say No Data Available",
                data_file="./core/data/test_files/test_no_labels.csv",
                label_list=["about cats", "not about cats", "unclear"],
                perm_list=[],
                classifier="logistic regression",
            )

            print("Seeding labels...")
            for _ in range(3):
                label_project(
                    root_project, root_profile, root_project.labels.count() * 10
                )

            label_project(
                multi_user_project, root_profile, multi_user_project.labels.count() * 10
            )
            label_project(
                multi_user_project, tom_profile, multi_user_project.labels.count() * 10
            )
            label_project(
                multi_user_project, jade_profile, multi_user_project.labels.count() * 10
            )

        print("Finished seeding database.")
