from django.conf.urls import include, re_path
from rest_framework import routers

from core.views import api, api_admin, api_annotate, api_viewsets

app_name = "core"

api_router = routers.DefaultRouter()
api_router.register(r"users", api_viewsets.ProfileViewSet)
api_router.register(r"auth_users", api_viewsets.AuthUserViewSet)
api_router.register(r"auth_groups", api_viewsets.AuthUserGroupViewSet)
api_router.register(r"projects", api_viewsets.ProjectViewSet)
api_router.register(r"models", api_viewsets.CoreModelViewSet)
api_router.register(r"labels", api_viewsets.LabelViewSet)
api_router.register(r"data", api_viewsets.DataViewSet)
api_router.register(r"data_labels", api_viewsets.DataLabelViewSet)
api_router.register(r"data_predictions", api_viewsets.DataPredictionViewSet)
api_router.register(r"queue", api_viewsets.QueueViewSet)
api_router.register(r"assigned_data", api_viewsets.AssignedDataViewSet)

annotate_patterns = [
    re_path(
        r"^label_distribution_inverted/(?P<project_pk>\d+)/$",
        api_annotate.label_distribution_inverted,
    ),
    re_path(
        r"^check_admin_in_progress/(?P<project_pk>\d+)/$",
        api_annotate.check_admin_in_progress,
    ),
    re_path(r"^restore_data/(?P<data_pk>\d+)/$", api_annotate.restore_data),
    re_path(r"^discard_data/(?P<data_pk>\d+)/$", api_annotate.discard_data),
    re_path(r"^annotate_data/(?P<data_pk>\d+)/$", api_annotate.annotate_data),
    re_path(r"^modify_label/(?P<data_pk>\d+)/$", api_annotate.modify_label),
    re_path(
        r"^modify_label_to_skip/(?P<data_pk>\d+)/$", api_annotate.modify_label_to_skip
    ),
    re_path(r"^skip_data/(?P<data_pk>\d+)/$", api_annotate.skip_data),
    re_path(
        r"^enter_coding_page/(?P<project_pk>\d+)/$", api_annotate.enter_coding_page
    ),
    re_path(
        r"^leave_coding_page/(?P<project_pk>\d+)/$", api_annotate.leave_coding_page
    ),
    re_path(
        r"^data_unlabeled_table/(?P<project_pk>\d+)/$",
        api_annotate.data_unlabeled_table,
    ),
    re_path(r"^get_card_deck/(?P<project_pk>\d+)/$", api_annotate.get_card_deck),
    re_path(
        r"^recycle_bin_table/(?P<project_pk>\d+)/$", api_annotate.recycle_bin_table
    ),
    re_path(
        r"^get_label_history/(?P<project_pk>\d+)/$", api_annotate.get_label_history
    ),
    re_path(r"^label_skew_label/(?P<data_pk>\d+)/$", api_annotate.label_skew_label),
    re_path(r"^label_admin_label/(?P<data_pk>\d+)/$", api_annotate.label_admin_label),
    re_path(r"^data_admin_table/(?P<project_pk>\d+)/$", api_annotate.data_admin_table),
    re_path(
        r"^data_admin_counts/(?P<project_pk>\d+)/$", api_annotate.data_admin_counts
    ),
]

adminpage_patterns = [
    re_path(r"^label_distribution/(?P<project_pk>\d+)/$", api_admin.label_distribution),
    re_path(r"^label_timing/(?P<project_pk>\d+)/$", api_admin.label_timing),
    re_path(r"^model_metrics/(?P<project_pk>\d+)/$", api_admin.model_metrics),
    re_path(r"^data_coded_table/(?P<project_pk>\d+)/$", api_admin.data_coded_table),
    re_path(
        r"^data_predicted_table/(?P<project_pk>\d+)/$", api_admin.data_predicted_table
    ),
    re_path(r"^get_irr_metrics/(?P<project_pk>\d+)/$", api_admin.get_irr_metrics),
    re_path(r"^heat_map_data/(?P<project_pk>\d+)/$", api_admin.heat_map_data),
    re_path(r"^perc_agree_table/(?P<project_pk>\d+)/$", api_admin.perc_agree_table),
]

urlpatterns = [
    re_path(r"^", include(api_router.urls)),
    # re_path(r"^progressbarupload/", include("progressbarupload.urls")),
    re_path(r"^download_data/(?P<project_pk>\d+)/$", api.download_data),
    re_path(r"^download_model/(?P<project_pk>\d+)/$", api.download_model),
    re_path(r"^", include(annotate_patterns)),
    re_path(r"^", include(adminpage_patterns)),
]
