package main

import (
	"context"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func TestMain(m *testing.M) {
	gin.SetMode(gin.TestMode)
	os.Exit(m.Run())
}

func seedStore() *UserStore {
	return NewUserStore([]User{
		{ID: "1", Name: "Alice", Age: 30},
		{ID: "2", Name: "Bob", Age: 35},
	})
}

func performRequest(r http.Handler, method, path string) *httptest.ResponseRecorder {
	req, _ := http.NewRequestWithContext(context.Background(), method, path, nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	return w
}

func TestGetUsers(t *testing.T) {
	t.Parallel()

	router := setupRouter(seedStore())
	w := performRequest(router, "GET", "/users")

	assert.Equal(t, http.StatusOK, w.Code)

	expected := `[{"id":"1","name":"Alice","age":30},{"id":"2","name":"Bob","age":35}]`
	assert.Equal(t, expected, w.Body.String())
}

func TestGetUser(t *testing.T) {
	t.Parallel()

	router := setupRouter(seedStore())
	w := performRequest(router, "GET", "/users/1")

	assert.Equal(t, http.StatusOK, w.Code)

	expected := `{"id":"1","name":"Alice","age":30}`
	assert.Equal(t, expected, w.Body.String())
}

func TestGetUserNotFound(t *testing.T) {
	t.Parallel()

	router := setupRouter(seedStore())
	w := performRequest(router, "GET", "/users/3")

	assert.Equal(t, http.StatusNotFound, w.Code)

	expected := `{"error":"User not found"}`
	assert.Equal(t, expected, w.Body.String())
}

func TestCreateUser(t *testing.T) {
	t.Parallel()

	router := setupRouter(seedStore())

	payload := `{"id":"3","name":"Charlie","age":25}`
	reader := strings.NewReader(payload)

	req, _ := http.NewRequestWithContext(context.Background(), http.MethodPost, "/users", reader)
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusCreated, w.Code)
	assert.Contains(t, w.Body.String(), "Charlie")
}
