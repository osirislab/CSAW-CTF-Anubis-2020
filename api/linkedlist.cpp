#include <iostream>
#include <vector>

class Node {
public:
  Node* next;
  int data;

  Node(int data) : next(NULL), data(data) {}
  Node(int data, Node* next) : next(next), data(data) {}
  ~Node() {
    delete this;
  }

  void setNext(Node* next) {
    this->next = next;
  }

};

std::ostream& operator<<(std::ostream& os, Node* head) {
  os << head->data;
  if (head->next != NULL) {
    os << "->";
    return operator<<(os, head->next);
  }
  return os;
}

int main() {
  Node* head1 = new Node(7, new Node(5, new Node(8)));
  Node* head2 = new Node(9, new Node(3, new Node(7)));
  std::cout << head1 << std::endl;
  std::cout << head2 << std::endl;

  // START TODO merge and sort lists into head3
  Node* head3 = NULL;


  // END TODO

  if (head3 != NULL) {
    std::cout << head3 << std::endl;
  }
}
