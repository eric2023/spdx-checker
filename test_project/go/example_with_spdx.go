/*
SPDX-License-Identifier: MIT
Copyright (c) 2025 Example Corporation

This is a Go file with proper SPDX license declaration.
*/

package main

import (
	"fmt"
	"log"
	"net/http"
)

// Config represents application configuration
type Config struct {
	Port        int
	DatabaseURL string
	Debug       bool
}

// Server represents the HTTP server
type Server struct {
	config Config
	logger *log.Logger
}

// NewServer creates a new server instance
func NewServer(config Config, logger *log.Logger) *Server {
	return &Server{
		config: config,
		logger: logger,
	}
}

// Start starts the HTTP server
func (s *Server) Start() error {
	http.HandleFunc("/", s.homeHandler)
	addr := fmt.Sprintf(":%d", s.config.Port)
	s.logger.Printf("Starting server on %s", addr)
	return http.ListenAndServe(addr, nil)
}

func (s *Server) homeHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html")
	fmt.Fprintf(w, "<h1>SPDX Scanner Go Example</h1>")
	fmt.Fprintf(w, "<p>Port: %d</p>", s.config.Port)
	fmt.Fprintf(w, "<p>Debug: %t</p>", s.config.Debug)
}

func main() {
	config := Config{
		Port:        8080,
		DatabaseURL: "postgres://localhost:5432/mydb",
		Debug:       true,
	}

	logger := log.New(os.Stdout, "[SPDX-Scanner] ", log.LstdFlags)
	server := NewServer(config, logger)

	if err := server.Start(); err != nil {
		log.Fatal(err)
	}
}