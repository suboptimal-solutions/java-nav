package com.example.processor;

public class EmailProcessor extends AbstractProcessor {
    @Override
    public void process(String message) {
        log("Sending email: " + message);
    }
}
