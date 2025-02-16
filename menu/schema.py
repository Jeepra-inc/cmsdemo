import graphene
from graphene_django.types import DjangoObjectType
from .models import Menu


class MenuType(DjangoObjectType):
    class Meta:
        model = Menu
        fields = ("id", "menu_name", "menu_data", "created_at")


class Query(graphene.ObjectType):
    menus = graphene.List(MenuType)

    def resolve_menus(self, info):
        return Menu.objects.all()


class CreateMenu(graphene.Mutation):
    class Arguments:
        menu_name = graphene.String(required=True)
        menu_data = graphene.JSONString()

    menu = graphene.Field(MenuType)

    def mutate(self, info, menu_name, menu_data=None):
        menu = Menu.objects.create(menu_name=menu_name, menu_data=menu_data)
        return CreateMenu(menu=menu)


class Mutation(graphene.ObjectType):
    create_menu = CreateMenu.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
