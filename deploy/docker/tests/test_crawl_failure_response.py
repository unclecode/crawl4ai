def test_all_failed_crawl_returns_results(stock_client, server_module, monkeypatch):
    async def failed_crawl(**kwargs):
        return {
            "success": True,
            "results": [
                {
                    "url": "https://example.com",
                    "success": False,
                    "error_message": "Wait condition failed: selector not found",
                }
            ],
        }

    monkeypatch.setattr(server_module, "handle_crawl_request", failed_crawl)

    from auth import create_access_token

    token = create_access_token({"sub": "test@example.com"})
    response = stock_client.post(
        "/crawl",
        json={"urls": ["https://example.com"]},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["success"] is False
    assert "Wait condition failed" in result["error_message"]
