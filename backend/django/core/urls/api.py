from django.conf.urls import url, include
from rest_framework import routers
from core.views import api, api_viewsets, api_annotate, api_admin


api_router = routers.DefaultRouter()
api_router.register(r'users', api_viewsets.ProfileViewSet)
api_router.register(r'auth_users', api_viewsets.AuthUserViewSet)
api_router.register(r'auth_groups', api_viewsets.AuthUserGroupViewSet)
api_router.register(r'projects', api_viewsets.ProjectViewSet)
api_router.register(r'models', api_viewsets.CoreModelViewSet)
api_router.register(r'labels', api_viewsets.LabelViewSet)
api_router.register(r'data', api_viewsets.DataViewSet)
api_router.register(r'data_labels', api_viewsets.DataLabelViewSet)
api_router.register(r'data_predictions', api_viewsets.DataPredictionViewSet)
api_router.register(r'queue', api_viewsets.QueueViewSet)
api_router.register(r'assigned_data', api_viewsets.AssignedDataViewSet)

annotate_patterns = [
    url(r'^label_distribution_inverted/(?P<project_pk>\d+)/$', api_annotate.label_distribution_inverted),
    url(r'^check_admin_in_progress/(?P<project_pk>\d+)/$', api_annotate.check_admin_in_progress),
    url(r'^restore_data/(?P<data_pk>\d+)/$', api_annotate.restore_data),
    url(r'^discard_data/(?P<data_pk>\d+)/$', api_annotate.discard_data),
    url(r'^annotate_data/(?P<data_pk>\d+)/$', api_annotate.annotate_data),
    url(r'^modify_label/(?P<data_pk>\d+)/$', api_annotate.modify_label),
    url(r'^modify_label_to_skip/(?P<data_pk>\d+)/$', api_annotate.modify_label_to_skip),
    url(r'^skip_data/(?P<data_pk>\d+)/$', api_annotate.skip_data),
    url(r'^enter_coding_page/(?P<project_pk>\d+)/$', api_annotate.enter_coding_page),
    url(r'^leave_coding_page/(?P<project_pk>\d+)/$', api_annotate.leave_coding_page),
    url(r'^data_unlabeled_table/(?P<project_pk>\d+)/$', api_annotate.data_unlabeled_table),
    url(r'^get_card_deck/(?P<project_pk>\d+)/$', api_annotate.get_card_deck),
    url(r'^recycle_bin_table/(?P<project_pk>\d+)/$', api_annotate.recycle_bin_table),
    url(r'^get_label_history/(?P<project_pk>\d+)/$', api_annotate.get_label_history),
    url(r'^label_skew_label/(?P<data_pk>\d+)/$', api_annotate.label_skew_label),
    url(r'^label_admin_label/(?P<data_pk>\d+)/$', api_annotate.label_admin_label),
    url(r'^data_admin_table/(?P<project_pk>\d+)/$', api_annotate.data_admin_table),
    url(r'^data_admin_counts/(?P<project_pk>\d+)/$', api_annotate.data_admin_counts),
]

adminpage_patterns = [
    url(r'^label_distribution/(?P<project_pk>\d+)/$', api_admin.label_distribution),
    url(r'^label_timing/(?P<project_pk>\d+)/$', api_admin.label_timing),
    url(r'^model_metrics/(?P<project_pk>\d+)/$', api_admin.model_metrics),
    url(r'^data_coded_table/(?P<project_pk>\d+)/$', api_admin.data_coded_table),
    url(r'^data_predicted_table/(?P<project_pk>\d+)/$', api_admin.data_predicted_table),
    url(r'^get_irr_metrics/(?P<project_pk>\d+)/$', api_admin.get_irr_metrics),
    url(r'^heat_map_data/(?P<project_pk>\d+)/$', api_admin.heat_map_data),
    url(r'^perc_agree_table/(?P<project_pk>\d+)/$', api_admin.perc_agree_table),
]

urlpatterns = [
    url(r'^', include(api_router.urls)),
    url(r'^progressbarupload/', include('progressbarupload.urls')),
    url(r'^download_data/(?P<project_pk>\d+)/$', api.download_data),
    url(r'^download_model/(?P<project_pk>\d+)/$', api.download_model),
    url(r'^', include(annotate_patterns)),
    url(r'^', include(adminpage_patterns)),
]
