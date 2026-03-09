use num_bigint::BigUint;

fn factorial(n: u32) -> BigUint {
    (1..=n).map(BigUint::from).product()
}

fn main() {
    println!("10! = {}", factorial(10));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_factorial_zero() {
        assert_eq!(factorial(0), BigUint::from(1u32));
    }

    #[test]
    fn test_factorial_five() {
        assert_eq!(factorial(5), BigUint::from(120u32));
    }

    #[test]
    fn test_factorial_ten() {
        assert_eq!(factorial(10), BigUint::from(3_628_800u32));
    }
}
