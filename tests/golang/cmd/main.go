// Package main provides a simple REST API for user management.
package main

import (
	"net/http"
	"sync"

	"github.com/gin-gonic/gin"
)

// User represents a user entity.
type User struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Age  int    `json:"age"`
}

// UserStore holds users with thread-safe access.
type UserStore struct {
	mu    sync.RWMutex
	users []User
}

func NewUserStore(initial []User) *UserStore {
	cp := make([]User, len(initial))
	copy(cp, initial)

	return &UserStore{users: cp}
}

func (s *UserStore) All() []User {
	s.mu.RLock()
	defer s.mu.RUnlock()

	cp := make([]User, len(s.users))
	copy(cp, s.users)

	return cp
}

func (s *UserStore) FindByID(id string) (User, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	for _, u := range s.users {
		if u.ID == id {
			return u, true
		}
	}

	return User{}, false
}

func (s *UserStore) Add(u User) {
	s.mu.Lock()
	defer s.mu.Unlock()

	s.users = append(s.users, u)
}

var defaultStore = NewUserStore([]User{
	{ID: "1", Name: "Alice", Age: 30},
	{ID: "2", Name: "Bob", Age: 35},
})

func main() {
	router := setupRouter(defaultStore)

	if err := router.Run(":8080"); err != nil {
		panic(err)
	}
}

func setupRouter(store *UserStore) *gin.Engine {
	router := gin.Default()

	router.GET("/users", getUsers(store))
	router.GET("/users/:id", getUser(store))
	router.POST("/users", createUser(store))

	return router
}

func getUsers(store *UserStore) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.JSON(http.StatusOK, store.All())
	}
}

func getUser(store *UserStore) gin.HandlerFunc {
	return func(c *gin.Context) {
		id := c.Param("id")

		if user, ok := store.FindByID(id); ok {
			c.JSON(http.StatusOK, user)
			return
		}

		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
	}
}

func createUser(store *UserStore) gin.HandlerFunc {
	return func(c *gin.Context) {
		var newUser User

		if err := c.BindJSON(&newUser); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		store.Add(newUser)

		c.JSON(http.StatusCreated, newUser)
	}
}
