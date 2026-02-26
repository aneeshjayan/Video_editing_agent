from unittest.mock import MagicMock, patch

import pytest

from core.exceptions import VisionServiceError
from services.vision_service import (
    MoondreamCloudService,
    create_vision_service,
)


class TestMoondreamCloudService:
    @patch("services.vision_service.md")
    def test_caption_returns_text(self, mock_md):
        """Caption should return the caption string from Moondream."""
        mock_model = MagicMock()
        mock_model.caption.return_value = {"caption": "A dog playing in the park"}
        mock_md.vl.return_value = mock_model

        service = MoondreamCloudService(api_key="test-key")
        image = MagicMock()
        result = service.caption(image)

        assert result == "A dog playing in the park"
        mock_model.caption.assert_called_once_with(image)

    @patch("services.vision_service.md")
    def test_query_returns_answer(self, mock_md):
        """Query should return the answer string from Moondream."""
        mock_model = MagicMock()
        mock_model.query.return_value = {"answer": "Yes, there are 3 people"}
        mock_md.vl.return_value = mock_model

        service = MoondreamCloudService(api_key="test-key")
        image = MagicMock()
        result = service.query(image, "How many people are there?")

        assert result == "Yes, there are 3 people"

    @patch("services.vision_service.md")
    def test_caption_raises_on_error(self, mock_md):
        """Caption should wrap exceptions in VisionServiceError."""
        mock_model = MagicMock()
        mock_model.caption.side_effect = RuntimeError("API error")
        mock_md.vl.return_value = mock_model

        service = MoondreamCloudService(api_key="test-key")
        with pytest.raises(VisionServiceError, match="caption failed"):
            service.caption(MagicMock())


class TestCreateVisionService:
    @patch("services.vision_service.md")
    def test_creates_cloud_by_default(self, mock_md):
        """Factory should create cloud service when use_local is False."""
        mock_settings = MagicMock()
        mock_settings.moondream_use_local = False
        mock_settings.moondream_api_key = "test-key"

        service = create_vision_service(mock_settings)
        assert isinstance(service, MoondreamCloudService)

    @patch("services.vision_service.md")
    def test_creates_local_when_configured(self, mock_md):
        """Factory should create local service when use_local is True."""
        from services.vision_service import MoondreamLocalService

        mock_settings = MagicMock()
        mock_settings.moondream_use_local = True
        mock_settings.moondream_local_url = "http://localhost:2020"

        service = create_vision_service(mock_settings)
        assert isinstance(service, MoondreamLocalService)
