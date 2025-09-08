int One(int i);
int One0(int i = 0);
int Two(int i, int j);

namespace N {

struct C
{};

class A
{
public:
int One(int i);
int One0(int i = 0);
int Two(int i, int j);
void N(const C& c);
};

void main()
{
    A a;
    
    One0(0);
    if (One(1) > 0)
    { Two(1, 2); }
    One(
        One(1)
    );

    auto res = a.One(a.Two(1, 2));
}

}

void
N::A::N(const N::C& c)
{}