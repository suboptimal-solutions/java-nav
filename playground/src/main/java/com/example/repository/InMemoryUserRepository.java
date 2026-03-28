package com.example.repository;

import com.example.model.User;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

public class InMemoryUserRepository implements Repository<User> {
    private final Map<String, User> store = new ConcurrentHashMap<>();

    @Override
    public Optional<User> findById(String id) {
        return Optional.ofNullable(store.get(id));
    }

    @Override
    public List<User> findAll() {
        return new ArrayList<>(store.values());
    }

    @Override
    public void save(User entity) {
        store.put(entity.getId(), entity);
    }

    @Override
    public void delete(String id) {
        store.remove(id);
    }
}
