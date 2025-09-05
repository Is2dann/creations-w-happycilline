def bag_items_count(request):
    """ Expose total item count in the bag to all templates """
    bag = request.session.get('bag', {})
    try:
        return {'bag_items_count': sum(int(q) for q in bag.values())}
    except Exception:
        return {'bag_items_count': 0}