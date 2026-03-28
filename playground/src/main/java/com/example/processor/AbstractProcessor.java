package com.example.processor;

/**
 * Base class for testing "find subtypes".
 */
public abstract class AbstractProcessor {
    public abstract void process(String message);

    public void log(String message) {
        System.out.println("[" + getClass().getSimpleName() + "] " + message);
    }
}
