echo # Enterprise Knowledge Assistant 
echo This platform allows users to upload documents, split them into chunks, and perform RAG search with isolated user metadata. >>
curl -X POST http://127.0.0.1:8000/api/v1/ingest/ -H "Content-Type: application/json" -H "Authorization: Bearer <eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg0ODkyMjk0LCJpYXQiOjE3ODQ4OTE5OTQsImp0aSI6ImI3ZDk4NDAzNzFmNTQyYTViYmVlNzJlYThjYzIzN2UwIiwidXNlcl9pZCI6IjEifQ.CC7gGJiF_OYwUr8cCQCdY9tQOavH8vE4UKG3JEFAeMY>" -d "{\"directory\": \"data\"}"




curl -X POST http://127.0.0.1:8000/api/v1/supervisor/ -H "Content-Type: application/json" -H "Authorization: Bearer <eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg0ODkyMjk0LCJpYXQiOjE3ODQ4OTE5OTQsImp0aSI6ImI3ZDk4NDAzNzFmNTQyYTViYmVlNzJlYThjYzIzN2UwIiwidXNlcl9pZCI6IjEifQ.CC7gGJiF_OYwUr8cCQCdY9tQOavH8vE4UKG3JEFAeMY>" -d "{\"query\": \"What does this platform do?\"}"