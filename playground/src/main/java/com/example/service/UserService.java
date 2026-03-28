package com.example.service;

import com.example.model.User;
import com.example.repository.Repository;
import com.google.common.base.Preconditions;
import com.google.common.base.Strings;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public class UserService {
    private final Repository<User> repository;

    public UserService(Repository<User> repository) {
        this.repository = repository;
    }

    public User createUser(String name, String email) {
        Preconditions.checkArgument(!Strings.isNullOrEmpty(name), "name must not be empty");
        Preconditions.checkArgument(!Strings.isNullOrEmpty(email), "email must not be empty");

        User user = new User(UUID.randomUUID().toString(), name, email);
        repository.save(user);
        return user;
    }

    public Optional<User> getUser(String id) {
        return repository.findById(id);
    }

    public List<User> listUsers() {
        return repository.findAll();
    }

    public void deleteUser(String id) {
        Preconditions.checkArgument(!Strings.isNullOrEmpty(id), "id must not be empty");
        repository.delete(id);
    }
}
