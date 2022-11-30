def test_request_example(client):
    response = client.get("/ping")
    assert b"<h1>Hello, world!</h1>" in response.data
