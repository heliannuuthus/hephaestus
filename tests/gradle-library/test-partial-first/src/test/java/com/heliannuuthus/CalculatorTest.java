package com.heliannuuthus;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.heliannuuthus.Calculator;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

class CalculatorTest {

  @Test
  void testAdd() {
    Calculator calculator = new Calculator();
    assertEquals(5, calculator.add(2, 3));
  }

  @Test
  void testSubtract() {
    Calculator calculator = new Calculator();
    assertEquals(1, calculator.subtract(3, 2));
  }

  @Test
  void testMultiply() {
    Calculator calculator = new Calculator();
    assertEquals(6, calculator.multiply(2, 3));
  }

  @Test
  void testDivide() {
    Calculator calculator = new Calculator();
    assertEquals(2, calculator.divide(6, 3));
  }

  @Test()
  void testDivideByZero() {
    Calculator calculator = new Calculator();

    Assertions.assertThrows(
        IllegalArgumentException.class,
        () -> {
          calculator.divide(6, 0);
        });
  }
}
