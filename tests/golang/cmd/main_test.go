package main

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

func performRequest(r http.Handler, method, path string) *httptest.ResponseRecorder {
	req, _ := http.NewRequestWithContext(context.Background(), method, path, nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	return w
}

func TestGetUsers(t *testing.T) {
	t.Parallel()

	router := gin.Default()
	gin.SetMode(gin.DebugMode)
	router.GET("/users", getUsers)

	w := performRequest(router, "GET", "/users")

	assert.Equal(t, http.StatusOK, w.Code)

	expected := `[{"id":"1","name":"Alice","age":30},{"id":"2","name":"Bob","age":35}]`
	assert.Equal(t, expected, w.Body.String())
}

func TestGetUser(t *testing.T) {
	t.Parallel()

	router := gin.Default()
	router.GET("/users/:id", getUser)

	w := performRequest(router, "GET", "/users/1")

	assert.Equal(t, http.StatusOK, w.Code)

	expected := `{"id":"1","name":"Alice","age":30}`
	assert.Equal(t, expected, w.Body.String())
}

func TestGetUserNotFound(t *testing.T) {
	t.Parallel()

	router := gin.Default()
	router.GET("/users/:id", getUser)

	w := performRequest(router, "GET", "/users/3")

	assert.Equal(t, http.StatusNotFound, w.Code)

	expected := `{"error":"User not found"}`
	assert.Equal(t, expected, w.Body.String())
}

func TestCreateUser(t *testing.T) {
	t.Parallel()

	router := gin.Default()
	router.POST("/users", createUser)

	payload := `{"id":"3","name":"Charlie","age":25}`
	reader := strings.NewReader(payload)

	req, _ := http.NewRequestWithContext(context.Background(), "POST", "/users", reader)
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	router.ServeHTTP(w, req)

	assert.Equal(t, http.StatusCreated, w.Code)
	assert.Contains(t, w.Body.String(), "Charlie")
}
