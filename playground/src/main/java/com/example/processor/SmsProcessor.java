package com.example.processor;

public class SmsProcessor extends AbstractProcessor {
    @Override
    public void process(String message) {
        log("Sending SMS: " + message);
    }
}
