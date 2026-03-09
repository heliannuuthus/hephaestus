// Package main provides a simple REST API for user management.
package main

import (
	"net/http"

	"github.com/gin-gonic/gin"
)

// User represents a user entity.
type User struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	Age  int    `json:"age"`
}

var users = []User{
	{ID: "1", Name: "Alice", Age: 30},
	{ID: "2", Name: "Bob", Age: 35},
}

func main() {
	router := gin.Default()

	router.GET("/users", getUsers)
	router.GET("/users/:id", getUser)
	router.POST("/users", createUser)

	if err := router.Run(":8080"); err != nil {
		panic(err)
	}
}

func getUsers(c *gin.Context) {
	c.JSON(http.StatusOK, users)
}

func getUser(c *gin.Context) {
	id := c.Param("id")

	for _, user := range users {
		if user.ID == id {
			c.JSON(http.StatusOK, user)

			return
		}
	}

	c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
}

func createUser(c *gin.Context) {
	var newUser User

	if err := c.BindJSON(&newUser); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})

		return
	}

	newUser.ID = newUser.ID
	users = append(users, newUser)

	c.JSON(http.StatusCreated, newUser)
}
