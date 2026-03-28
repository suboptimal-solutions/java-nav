package com.example.repository;

import com.example.model.User;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * A second Repository implementation for testing "find implementations".
 */
public class FileUserRepository implements Repository<User> {
    private final List<User> store = new ArrayList<>();

    @Override
    public Optional<User> findById(String id) {
        return store.stream().filter(u -> u.getId().equals(id)).findFirst();
    }

    @Override
    public List<User> findAll() {
        return new ArrayList<>(store);
    }

    @Override
    public void save(User entity) {
        delete(entity.getId());
        store.add(entity);
    }

    @Override
    public void delete(String id) {
        store.removeIf(u -> u.getId().equals(id));
    }
}
