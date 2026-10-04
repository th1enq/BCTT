#pragma once

#include <algorithm>
#include <bit>
#include <cstdint>
#include <iomanip>
#include <ostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace tp {

// Minimal non-negative arbitrary-precision integer. Counts never become negative.
// Base 2^32 keeps addition/multiplication and exact bit length straightforward.
class BigInt {
public:
    BigInt() = default;
    BigInt(std::uint64_t value) {
        if (value == 0) return;
        words_.push_back(static_cast<std::uint32_t>(value));
        if (value >> 32U) words_.push_back(static_cast<std::uint32_t>(value >> 32U));
    }

    BigInt& operator+=(const BigInt& other) {
        const std::size_t size = std::max(words_.size(), other.words_.size());
        words_.resize(size, 0);
        std::uint64_t carry = 0;
        for (std::size_t i = 0; i < size; ++i) {
            const std::uint64_t rhs = i < other.words_.size() ? other.words_[i] : 0;
            const std::uint64_t sum = static_cast<std::uint64_t>(words_[i]) + rhs + carry;
            words_[i] = static_cast<std::uint32_t>(sum);
            carry = sum >> 32U;
        }
        if (carry) words_.push_back(static_cast<std::uint32_t>(carry));
        return *this;
    }

    BigInt& operator*=(std::uint32_t factor) {
        if (factor == 0 || words_.empty()) { words_.clear(); return *this; }
        std::uint64_t carry = 0;
        for (std::uint32_t& word : words_) {
            const std::uint64_t product = static_cast<std::uint64_t>(word) * factor + carry;
            word = static_cast<std::uint32_t>(product);
            carry = product >> 32U;
        }
        if (carry) words_.push_back(static_cast<std::uint32_t>(carry));
        return *this;
    }

    BigInt& operator/=(std::uint32_t divisor) {
        if (divisor == 0) throw std::domain_error("BigInt division by zero");
        std::uint64_t remainder = 0;
        for (std::size_t i = words_.size(); i-- > 0;) {
            const std::uint64_t current = (remainder << 32U) | words_[i];
            words_[i] = static_cast<std::uint32_t>(current / divisor);
            remainder = current % divisor;
        }
        normalize();
        if (remainder != 0) throw std::domain_error("non-exact BigInt division");
        return *this;
    }

    [[nodiscard]] std::uint64_t bit_length() const {
        if (words_.empty()) return 0;
        return 32ULL * (words_.size() - 1) + (32U - std::countl_zero(words_.back()));
    }

    [[nodiscard]] std::string str() const {
        if (words_.empty()) return "0";
        BigInt copy = *this;
        std::vector<std::uint32_t> chunks;
        while (!copy.words_.empty()) chunks.push_back(copy.divide_with_remainder(1'000'000'000U));
        std::ostringstream out;
        out << chunks.back();
        for (std::size_t i = chunks.size() - 1; i-- > 0;) out << std::setw(9) << std::setfill('0') << chunks[i];
        return out.str();
    }

    friend BigInt operator+(BigInt lhs, const BigInt& rhs) { lhs += rhs; return lhs; }

    friend BigInt operator*(const BigInt& lhs, const BigInt& rhs) {
        if (lhs.words_.empty() || rhs.words_.empty()) return {};
        BigInt result;
        result.words_.assign(lhs.words_.size() + rhs.words_.size(), 0);
        for (std::size_t i = 0; i < lhs.words_.size(); ++i) {
            std::uint64_t carry = 0;
            for (std::size_t j = 0; j < rhs.words_.size(); ++j) {
                const std::size_t k = i + j;
                const std::uint64_t product = static_cast<std::uint64_t>(lhs.words_[i]) * rhs.words_[j]
                                            + result.words_[k] + carry;
                result.words_[k] = static_cast<std::uint32_t>(product);
                carry = product >> 32U;
            }
            std::size_t k = i + rhs.words_.size();
            while (carry != 0) {
                const std::uint64_t sum = static_cast<std::uint64_t>(result.words_[k]) + carry;
                result.words_[k] = static_cast<std::uint32_t>(sum);
                carry = sum >> 32U;
                ++k;
                if (k == result.words_.size() && carry) result.words_.push_back(0);
            }
        }
        result.normalize();
        return result;
    }

    friend BigInt operator*(std::uint32_t lhs, BigInt rhs) { rhs *= lhs; return rhs; }
    friend BigInt operator*(BigInt lhs, std::uint32_t rhs) { lhs *= rhs; return lhs; }
    friend bool operator==(const BigInt&, const BigInt&) = default;
    friend bool operator==(const BigInt& lhs, std::uint64_t rhs) { return lhs == BigInt(rhs); }
    friend bool operator==(std::uint64_t lhs, const BigInt& rhs) { return rhs == lhs; }
    friend std::ostream& operator<<(std::ostream& out, const BigInt& value) { return out << value.str(); }

private:
    std::vector<std::uint32_t> words_;

    void normalize() {
        while (!words_.empty() && words_.back() == 0) words_.pop_back();
    }

    std::uint32_t divide_with_remainder(std::uint32_t divisor) {
        std::uint64_t remainder = 0;
        for (std::size_t i = words_.size(); i-- > 0;) {
            const std::uint64_t current = (remainder << 32U) | words_[i];
            words_[i] = static_cast<std::uint32_t>(current / divisor);
            remainder = current % divisor;
        }
        normalize();
        return static_cast<std::uint32_t>(remainder);
    }
};

} // namespace tp

