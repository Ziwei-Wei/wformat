// Pattern source: switch-based enum -> textual form (helper_macros streaming)
#include <iostream>
#include <cstdint>

enum class State : uint8_t
{
    Idle,
    Busy,
    Error,
    Unknown = 0xFF
};

std::ostream&
operator<<(
    std::ostream& os,
    State s
    )
{
    switch (s)
    {
        case State::Idle: return os << "Idle";
        case State::Busy: return os << "Busy";
        case State::Error: return os << "Error";
        default: return os << static_cast<unsigned>(static_cast<uint8_t>(s));
    }
}

int
main()
{
    std::cout << State::Busy << '\n';
}