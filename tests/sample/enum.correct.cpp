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

enum class StartMode : uint8_t // the mode when the remote session window shows the first time
{
    WindowedMode,
    FullscreenMode
} startMode = StartMode::FullscreenMode;

int
main()
{
    std::cout << State::Busy << '\n';
}