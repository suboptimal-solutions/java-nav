package com.example;

import com.example.model.User;
import com.example.repository.InMemoryUserRepository;
import com.example.service.UserService;

public class App {
    public static void main(String[] args) {
        var repo = new InMemoryUserRepository();
        var service = new UserService(repo);

        User alice = service.createUser("Alice", "alice@example.com");
        User bob = service.createUser("Bob", "bob@example.com");

        System.out.println("All users:");
        service.listUsers().forEach(System.out::println);

        System.out.println("\nLookup Alice: " + service.getUser(alice.getId()));

        service.deleteUser(bob.getId());
        System.out.println("\nAfter deleting Bob:");
        service.listUsers().forEach(System.out::println);
    }
}
