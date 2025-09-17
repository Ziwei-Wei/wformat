#include <stdio.h>

struct IConnectedArgs
{};

#define TRACE_INFORMATION(task, msg) printf("[%s] %s\n", task, msg)

struct ConnectionSettings
{
    void*
    SessionWindowHandle() const
    {
        return nullptr;
    }
};

struct IConnection
{
    ConnectionSettings
    ConnectionSettings() const
    {
        return {};
    }

    template <typename Handler>
    int
    Connected(
        Handler&& handler
        ) const
    {
        handler(
            *this,
            ::IConnectedArgs
            {
            }
            );

        return 1;
    }
};

int
main()
{
    IConnection connection {};

    auto connectedToken = connection.Connected(
        [] (const IConnection& sender, const IConnectedArgs& /*args*/)
        {
            TRACE_INFORMATION(
                "",
                "OnConnected"
                );
        }
        );

    printf(
        "connectedToken: %d\n",
        connectedToken
        );

    return 0;
}