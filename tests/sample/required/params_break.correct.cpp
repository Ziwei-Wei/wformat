int
One(int i);

int
One0(int i = 0);

int
Two(
    int i,
    int j
    );

class A
{
public:

    int
    One(int i);

    int
    One0(int i = 0);

    int
    Two(
        int i,
        int j
        );
};

int
main()
{
    A a;
    One(1);
    Two(
        1,
        2
        );
    One(
        One(1)
        );
    a.One(
        a.Two(
            1,
            2
            )
        );
}