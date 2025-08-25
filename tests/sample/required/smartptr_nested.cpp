#include <memory>
#include <iostream>

#define DECLARE_SMARTPOINTER(T) class T; using T##Ptr=std::shared_ptr<T>;

class DeviceBase {
public: virtual ~DeviceBase()=default; virtual void Activate()=0;
};

DECLARE_SMARTPOINTER(Device)

class Device final : public DeviceBase {
public:
    class Stats { public: int activates=0; };
    void Activate() override { ++_stats.activates; }
    const Stats& GetStats() const { return _stats; }
private:
    Stats _stats;
};

int main() {
    DevicePtr d = std::make_shared<Device>();
    d->Activate();
    std::cout << d->GetStats().activates << '\n';
}